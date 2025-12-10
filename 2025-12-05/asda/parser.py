import logging
import json
from curl_cffi import requests
from parsel import Selector
from pymongo import MongoClient
from settings import MONGO_DB, MONGO_COLLECTION_PRODUCTS, MONGO_COLLECTION_DATA,HEADERS, extra_headers,params


class Parser:
    """parser"""
    
    def __init__(self):
        self.mongo = MongoClient('mongodb://localhost:27017/')
    
    def start(self):
        """start code"""
        
        db = self.mongo[MONGO_DB]
        
        # Fetch all products from MongoDB
        products = db[MONGO_COLLECTION_PRODUCTS].aggregate([
            {"$sample": {"size": 300}}   # <-- random selection
        ])
        
        for product in products:
            url = product.get('url')
            if not url:
                continue
            
            logging.info(f"Processing: {url}")
            
            try:
                response = requests.get(url, headers=HEADERS, impersonate="chrome")
                if response and response.status_code == 200:
                    self.parse_item(url, response, product)
                else:
                    logging.error(f"Failed to fetch {url}: {response.status_code if response else 'No response'}")
                    # self.queue.publish(url)##########used for requeuing
            except Exception as e:
                logging.error(f"Error fetching {url}: {e}")
                # self.queue.publish(url)##########used for requeuing
    
    def close(self):
        """connection close"""
        self.mongo.close()
        # self.queue.close()
    
    def get_breadcrumbs_and_upc(self, product_id):
        API_URL = f"https://www.asda.com/mobify/proxy/ghs-api/product/shopper-products/v1/organizations/f_ecom_bjgs_prd/products/{product_id}"
        

        response = requests.get(API_URL, params=params, headers=extra_headers, impersonate="chrome")
        print("Status:", response.status_code)

        data = response.json()

        # Extract categories
        categories = data.get("c_categoryTree", {}).get("parentCategoryTree", [])
        category_names = [c.get("name") for c in categories]

        breadcrumb_path = " > ".join(category_names)

        # Final breadcrumb
        breadcrumbs = f"home > {breadcrumb_path} > {data.get('brand')} {data.get('name')}"

        # Get UPC
        upc = data.get("upc")

        return breadcrumbs, upc
    
    def parse_item(self, url, response, product):
        """item part"""
        sel = Selector(text=response.text)
        
        # XPATH
        DESCRIPTION_CONTAINER_XPATH = "//div[@class='css-1qm1lh']"
        IMAGE_SCRIPT_XPATH = "//script[@type='application/ld+json']//text()"
        
        # EXTRACT
        description_container = sel.xpath(DESCRIPTION_CONTAINER_XPATH)
        image_script = sel.xpath(IMAGE_SCRIPT_XPATH).get()
        wasprice=sel.xpath("//p[@class='chakra-text css-rba90p']//text()").get()
        # Parse description sections
        description_data = {}
        for des in description_container:
            keys = des.xpath('.//p[@class="chakra-text css-3gxl7s"]')
            
            for key_node in keys:
                key = key_node.xpath('normalize-space()').get()
                
                if key:
                    # Find value nodes (section content)
                    value_nodes = des.xpath(
                        './/p[@class="chakra-text css-1p1nmwo" '
                        'or @class="chakra-text css-810szs" '
                        'or @class="chakra-text css-133cdwn"]'
                    ) 
                    # Join all text inside the container
                    values = [
                        v.xpath('normalize-space()').get()
                        for v in value_nodes
                        if v.xpath('normalize-space()').get()
                    ]
                    
                    if values:
                        description_data[key] = " ".join(values)
        
        # Parse images from JSON-LD script
        images = []
        if image_script:
            json_data = json.loads(image_script)
            image=json_data.get("image")
            
        wasprice=wasprice.replace('css-16oo0ol{display:inline-block;font-size:0px;line-height:0;height:0px;-webkit-clip-path:inset(0 0 0 0);clip-path:inset(0 0 0 0);}','').replace("was","").strip() if wasprice else ""
       

       # Select the main nutrition section container
        nutrition_section = sel.xpath('//div[@class="css-z3gk3"]')
        if nutrition_section:
            # Extract heading: "Typical values per 100g"
            typical_values_text = nutrition_section.xpath('.//p[@class="chakra-text css-1p1nmwo"]/text()').get()
            typical_values_text = typical_values_text.strip() if typical_values_text else ""

            # Extract table rows from only inside css-z3gk3
            rows = nutrition_section.xpath('.//table//tr')

            nutritional_values = []

            for row in rows:
                cells = row.xpath(
                    './/p[@class="chakra-text css-1p1nmwo"]//text() | '
                    './/p[@class="chakra-text css-7usuug"]//text()'
                ).getall()
                cells = [c.strip() for c in cells if c.strip()]
                if cells:
                    nutritional_values.append(" - ".join(cells))

            # Build final paragraph
            nutritional_paragraph = f"{typical_values_text or ''}. {' ,'.join(nutritional_values)}"

        else:
            nutritional_paragraph=""

        breadcrumbs, upc = self.get_breadcrumbs_and_upc(product.get("product_id"))
        frozen=sel.xpath("//p[@class='chakra-text css-h8kb8s']/text()").get()
        allergy = ""

        # try to extract allergy info
        allergy_1 = sel.xpath("(//div[@class='chakra-skeleton css-8140fd'])[1]//p//text()").getall()
        allergy_2 = sel.xpath("(//div[@class='chakra-skeleton css-8140fd'])[2]//p//text()").getall()

        # only join if data exists
        parts = []
        if allergy_1:
            parts.append(" ".join(allergy_1).strip())
        if allergy_2:
            parts.append(" ".join(allergy_2).strip())

        allergy = ", ".join(parts)  
        lifestyle=",".join(sel.xpath("(//div[@class='chakra-skeleton css-8140fd'])[3]//p//text()").getall())
        # ITEM YEILD
        item = {}
        item["url"] = url
        item["product_id"] = product.get("product_id")
        item["name"] = product.get("name")
        item["brand"] = product.get("brand")
        item["price"] = product.get("price")
        item["currency"] = product.get("currency")
        item["package_size"] = product.get("package_size")
        item["priceperuom"] = product.get("priceperuom")
        item["stock"] = product.get("stock")
        item["avg_rating"] = product.get("avg_rating")
        item["rating_count"] = product.get("rating_count")
        item["promos"] = product.get("promos")
        item["wasprice"] = product.get("wasprice") or wasprice
        item["offer"] = product.get("offer")
        item["category_id"] = product.get("category_id")
        item["category_name"] = product.get("category_name")
        item["description"] = description_data
        item["images"] = image
        item["nutritional_values"]= nutritional_paragraph
        item["breadcrumbs"]=breadcrumbs
        item["upc"]=upc
        item['frozen']=frozen if frozen else ""
        item['allergy']=allergy if allergy else ""
        item['lifestyle'] = lifestyle
        
        
        logging.info(item)
        
        db = self.mongo[MONGO_DB]
        try:
            db[MONGO_COLLECTION_DATA].insert_one(item)
        except Exception as e:
            logging.error(f"Failed to insert item: {e}")


if __name__ == "__main__":
    parser_obj = Parser()
    parser_obj.start()
    parser_obj.close()