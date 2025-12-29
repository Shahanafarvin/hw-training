import json
from parsel import Selector
from curl_cffi import requests
from pymongo import MongoClient
from settings import logging, MONGO_DB,MONGO_COLLECTION_PRODUCTS,MONGO_COLLECTION_DATA,MONGO_COLLECTION_URL_FAILED

class Parser:
    """parser"""
    
    def __init__(self):
        self.mongo = MongoClient('mongodb://localhost:27017/')
        self.db = self.mongo[MONGO_DB]
    
    def start(self):
        """start code"""
        products = self.db[MONGO_COLLECTION_PRODUCTS].find({})
        
        for product in products:
            url = product.get('url')
            if not url:
                continue
            meta = {
                'url': url,
                'product_name': product.get('name'),
                'productNumber' : product.get('productNumber'),
                'stockNumber' : product.get('stockNumber'),
                'upc' : product.get('upc'),
                
            }
            logging.info(f"Parsing: {url}")
            
            try:
                response = requests.get(url, impersonate="chrome")
                if response.status_code == 200:
                    self.parse_item(url, response, meta)
                else:
                    self.db[MONGO_COLLECTION_URL_FAILED].insert_one({'url': url, 'status_code': response.status_code})
            except Exception as e:
                logging.error(f"Error fetching {url}: {e}")
   
    
    def parse_item(self, url, response, meta):
        """item part"""
        sel = Selector(text=response.text)
        
        # XPATH
        BREADCRUMBS_XPATH = "//ol[@class='MMM--breadcrumbs-list']/li//text()"
        HIGHLIGHTS_XPATH = "//li[@class='sps2-pdp_details--highlights_item mds-font_paragraph']//text()"
        DESCRIPTION_XPATH = "//div[@class='sps2-pdp_details--white_container']//text()"
        SUGGESTED_APP_XPATH = "//div[@class='sps2-pdp_details--section']//text()"
        SCRIPT_XPATH = "//script/text()"
        IMAGES_XPATH = "//div[@class='sps2-pdp_outerGallery--container']//img/@src"
        
        # EXTRACT
        breadcrumbs_list = sel.xpath(BREADCRUMBS_XPATH).getall()
        highlights_list = sel.xpath(HIGHLIGHTS_XPATH).getall()
        description_list = sel.xpath(DESCRIPTION_XPATH).getall()
        suggested_app_list = sel.xpath(SUGGESTED_APP_XPATH).getall()
        script_tags = sel.xpath(SCRIPT_XPATH).getall()
        images_list = sel.xpath(IMAGES_XPATH).getall()
        
        # CLEAN
        breadcrumb = " > ".join(breadcrumbs_list).strip() if breadcrumbs_list else ""
        breadcrumbs= " > ".join(part.strip() for part in breadcrumb.split(">") if part.strip())
        highlights = ", ".join(x.strip() for x in highlights_list if x.strip()) if highlights_list else ""
        description = ", ".join(x.strip() for x in description_list if x.strip()) if description_list else ""
        suggested_applications = ", ".join(x.strip() for x in suggested_app_list if x.strip()) if suggested_app_list else ""
        
        
        # Extract classification attributes from script
        classification_attributes = ""
        for script in script_tags:
            if script.startswith("window.__INITIAL_DATA ="):
            
                json_data = script.replace("window.__INITIAL_DATA = ", "").strip().rstrip(";")
                data = json.loads(json_data)
                classification_attributes = data.get("classificationAttributes", [])

                classification = {}

                for attr in classification_attributes:
                    label = attr.get("label")
                    values = attr.get("values", [])

                    assignments = ", ".join(v for v in values)
                    classification[label] = assignments

                colour=classification.get("Product Color", "")
                brands=classification.get("Brands", "")
                # Check for more images via API
                mediasize=data.get("mediaMoreCount")
                size=data.get("mediaOffset")
                if mediasize and size and mediasize!=0:
                    more_images = self.parse_moreimages(url,mediasize,size)
                    if more_images:
                        images_list.extend(more_images.split(", "))
                images=", ".join(images_list).strip() if images_list else ""
                # Extract document types
                documents=[]
                docs= data.get("resources",[])
                doc1=docs[0].get("originalUrl","") if docs else ""
                documents.append(doc1)
                document_type=data.get("resourcesAggs",[])
                if document_type:
                    typecodes=[]
                    for doc in document_type:
                        typecode=doc.get("typeCode","")
                        if typecode:
                            typecodes.append(typecode)
                    for t in typecodes[1:]:
                        doc=self.parse_moredocs(url,t)
                        documents.append(doc)
                    
            
        
        # ITEM YIELD
        item = {}
        item["product_name"] = meta.get("product_name")
        item["images"] = images
        item["pdp_url"] = url
        item["colour"] = colour
        item["brand"] = brands
        item["documents"] = ", ".join(documents)
        item["breadcrumbs"] = breadcrumbs
        item["highlights"] = highlights
        item["description"] = description
        item["suggested_applications"] = suggested_applications
        item["classification_attributes"] = classification
        item["product_number"] = meta.get("productNumber")
        item["stock_number"] = meta.get("stockNumber")
        item["upc"] = meta.get("upc")   
        
        #logging.info(item)
        
        try:
            self.db[MONGO_COLLECTION_DATA].insert_one(item)
        except:
            pass
    
    def parse_moreimages(self, url, mediasize, size):
        """Get more images from API"""
        url_parts = url.rstrip('/').split('/')
        product_id = url_parts[-1] if url_parts else None
        
        if not product_id:
            logging.warning(f"Could not extract product ID from {url}")
            return ""
        
        # Build API URL
        api_url = f"https://www.3m.com/snaps2/api/pdp/moreMedia/https/www.3m.com/3M/en_US/p/d/{product_id}/?mediaSize={mediasize}&start={size}"
        
        logging.info(f"Fetching more images from: {api_url}")
        
        response = requests.get(api_url, impersonate="chrome")
        
        if response.status_code == 200:
            data = response.json()
            media_items = data.get("media", [])
            
            image_urls = []
            for media in media_items:
                image_url = media.get("url")
                if image_url:
                    image_urls.append(image_url)
            
            images = ", ".join(image_urls) if image_urls else ""
            logging.info(f"Found {len(image_urls)} additional images")
            return images
        else:
            logging.warning(f"Failed to fetch more images: {response.status_code}")
            return ""
                
    def parse_moredocs(self, url, t):
        """Get documents/resources from API"""
        
        url_parts = url.rstrip('/').split('/')
        product_id = url_parts[-1] if url_parts else None
        
        if not product_id:
            logging.warning(f"Could not extract product ID from {url}")
            return ""
        
        # Build API URL
        api_url = f"https://www.3m.com/snaps2/api/pdp/moreResources/https/www.3m.com/3M/en_US/p/d/{product_id}/?size=4&start=0&{t}"
        
        logging.info(f"Fetching documents from: {api_url}")
        
        response = requests.get(api_url, impersonate="chrome")
        
        if response.status_code == 200:
            data = response.json()
            resources = data.get("resources", [])
            docs=resources[0].get("originalUrl","") if resources else ""
            return docs
        else:
            logging.warning(f"Failed to fetch documents: {response.status_code}")
            return ""
             
    def close(self):
        """connection close"""
        self.mongo.close()
        # self.queue.close()


if __name__ == "__main__":
    parser_obj = Parser()
    parser_obj.start()
    parser_obj.close()