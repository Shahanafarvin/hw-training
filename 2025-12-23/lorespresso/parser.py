import json
import requests
from parsel import Selector
from pymongo import MongoClient
from settings import MONGO_DB, MONGO_COLLECTION_PRODUCTS, MONGO_COLLECTION_DATA, MONGO_COLLECTION_URL_FAILED, logging

class Parser:
    """Parser for Lorespresso products"""
    
    def __init__(self):
        """Initialize MongoDB connection"""
        self.client= MongoClient('mongodb://localhost:27017/')
        self.mongo = self.client[MONGO_DB]
        
    
    def start(self):
        """Start parsing products"""
        
        # Fetch products from MongoDB
        products = self.mongo[MONGO_COLLECTION_PRODUCTS].find({})
        product_list = list(products)
        
        if not product_list:
            logging.warning("No products found in database")
            return
        
        logging.info(f"Found {len(product_list)} products to parse")
        
        for product_doc in product_list:
            url = product_doc.get('product_url')
            
            if not url:
                logging.warning(f"Skipping product with missing URL")
                continue
            
            meta = {
                'url': url,
                'sku': product_doc.get('sku'),
                'name': product_doc.get('name'),
                'price_range': product_doc.get('price_range'),
                'rating': product_doc.get('rating'),
                'review_count': product_doc.get('review_count'),
                
            }
            
            try:
                response = requests.get(url)
                
                if response.status_code == 200:
                    self.parse_item(meta, response)
                else:
                    logging.error(f"Failed to fetch URL: {url}, Status Code: {response.status_code}")
                    self.mongo[MONGO_COLLECTION_URL_FAILED].insert_one({'url': url, 'status_code': response.status_code})
                    
            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed for URL {url}: {e}")
    
    def parse_item(self, meta, response):
        """Parse product details"""
        sel = Selector(text=response.text)
        
        # XPATH
        DESCRIPTION_XPATH = "//div[@data-testid='product-description']//p/text()"
        BULLETS_XPATH = "//ul[@class='MuiList-root MuiList-padding brand-lor mui-style-1t9ifb2']/li//text()"
        JSON_LD_XPATH = '//script[@type="application/ld+json"]/text()'
        INCLUDED_XPATH= "//div[@class='MuiBox-root mui-style-c8qvxh']//text()"
        OFFERS_XPATH= '//div[@data-testid="offer-label"]//text()'
        SPECIFICATION_XPATH= "//tr[@class='MuiTableRow-root mui-style-kq3u83']"
        
        # EXTRACT
        description = sel.xpath(DESCRIPTION_XPATH).getall()
        bullets = sel.xpath(BULLETS_XPATH).getall()
        json_ld_scripts = sel.xpath(JSON_LD_XPATH).getall()
        #included=sel.xpath(INCLUDED_XPATH).getall()
        offer_label=sel.xpath(OFFERS_XPATH).get()
        specification_tr=sel.xpath(SPECIFICATION_XPATH)

        # CLEAN
        description = " ".join(x.strip() for x in description if x.strip()) if description else ""
        bullets = ",".join(x.strip() for x in bullets if x.strip()) if bullets else ""
        offer_label=offer_label.strip() if offer_label else ""
        #included = ",".join(x.strip() for x in included if x.strip()) if included else ""
        specifications = []

        for row in specification_tr:
            key = row.xpath(".//td[1]//text()").getall()
            value = row.xpath(".//td[2]//text()").getall()

            key = " ".join(k.strip() for k in key if k.strip())
            value = " ".join(v.strip() for v in value if v.strip())

            if key and value:
                specifications.append(f"{key}: {value}")

        specifications = ", ".join(specifications) if specifications else ""

        # Extract JSON-LD data
        product_data = None
        breadcrumb_data = None
        
        for script in json_ld_scripts:
            try:
                data = json.loads(script.strip())
                
                if isinstance(data, dict):
                    if data.get("@type") == "Product":
                        product_data = data
                    elif data.get("@type") == "BreadcrumbList":
                        breadcrumb_data = data
                        
            except json.JSONDecodeError:
                continue
        
        # Extract breadcrumbs
        breadcrumbs = ""
        if breadcrumb_data:
            breadcrumb_items = breadcrumb_data.get("itemListElement", [])
            
            # Sort by position
            breadcrumb_items = sorted(
                breadcrumb_items,
                key=lambda x: x.get("position", 0)
            )
            
            breadcrumbs = " > ".join(
                item.get("name", "").strip()
                for item in breadcrumb_items
                if item.get("name")
            )
        
        # Extract additional product data from JSON-LD
        images = []
        brand = "L'OR"
        
        if product_data:
            images = product_data.get("image", [])
            if isinstance(images, str):
                images = [images]
            
        # ITEM YIELD
        item = {}
        item["product_name"] = meta.get('name')
        item["images"] = images
        item["pdp_url"]= meta.get('url')
        item["brand"] = brand
        item["breadcrumbs"] = breadcrumbs
        item["rating"] = meta.get('rating')
        item["review"] = meta.get('review_count')
        item["key_features"]= bullets
        item["regular_price"]= meta.get('price_range').get("minimum_price").get("regular_price").get("value") 
        item["selling_price"]= meta.get('price_range').get("minimum_price").get("final_price").get("value")
        item["currency"]= meta.get('price_range').get("minimum_price").get("final_price").get("currency")
        item["description"]= description
        #item["more_details"]= included#more cleaning needed
        item["offer_label"]= offer_label
        item["specifications"]= specifications
        logging.info(item)
        
        try:
            self.mongo[MONGO_COLLECTION_DATA].insert_one(item)
        except Exception as e:
            logging.error(f"Failed to save parsed product {item.get('sku')}: {e}")
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()


if __name__ == "__main__":
    parser_obj = Parser()
    parser_obj.start()
    parser_obj.close()