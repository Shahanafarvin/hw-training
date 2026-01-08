import logging
import time
import requests
from pymongo import MongoClient
from settings import headers, LOCATIONS, get_cookies, get_json_data, MONGO_DB, MONGO_COLLECTION_PRODUCTS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Crawler:
    """Crawling JioMart Products"""
    
    def __init__(self):
        self.mongo_client = MongoClient('mongodb://localhost:27017/')
        self.mongo = self.mongo_client[MONGO_DB]
        self.mongo[MONGO_COLLECTION_PRODUCTS].create_index([("unique_id", 1), ("location_city", 1)],unique=True)
    
    def start(self):
        """Requesting Start url"""
        
        for location in LOCATIONS:
            meta = {}
            meta['location'] = location
            meta['city'] = location['city']
            meta['pincode'] = location['pincode']
            meta['state_code'] = location['state_code']
            meta['page'] = 1
            
            logging.info(f"Starting scrape for {location['city']} ({location['pincode']})")
            
            api_url = 'https://www.jiomart.com/trex/search'
            cookies = get_cookies(location['city'], location['pincode'], location['state_code'])
            json_data = get_json_data()
            
            while True:
                logging.info(f"[{meta['city']}] Fetching page {meta['page']}")
                
                response = requests.post(
                    api_url,
                    cookies=cookies,
                    headers=headers,
                    json=json_data
                )
                
                if response.status_code == 200:
                    is_next = self.parse_item(response, meta, json_data)
                    if not is_next:
                        logging.info(f"[{meta['city']}] Pagination completed")
                        break
                    
                    # pagination crawling
                    meta["page"] += 1
                    time.sleep(1) 
                else:
                    logging.error(f"[{meta['city']}] Request failed: {response.status_code}")
                    
                    break
            
    
    def parse_item(self, response, meta, json_data):
        """item part"""
        data = response.json()
        
        # Extract products
        products = data.get("results", [])
        
        if products:
            for product in products:
                variants = product.get("product", {}).get("variants", [])
                for variant in variants:
                    unique_id=variant.get("id") if variants else None
                    product_name=variant.get("title")
                    brand=variant.get("brands", [""])[0] if variant else None
                    url=variant.get("uri") if variant else None
                    food_type=variant.get("attributes", {}).get("food_type", {}).get("text") if variant else None
                    size=variant.get("sizes",[]
                                     )
                    # ITEM YIELD
                    item = {}
                    item['unique_id'] = unique_id
                    item['retailer_name'] = "jiomart"
                    item['extraction_date'] = time.strftime("%Y-%m-%d")
                    item['location_city'] = meta['city']
                    item['location_pincode'] = meta['pincode']
                    item['location_state'] = meta['state_code']
                    item['product_name'] = product_name
                    item["size"]=size
                    item['brand'] = brand
                    item['url'] = url
                    item['food_type'] = food_type
                    
                    logging.info(item)
                    
                    #Save to MongoDB (optional)
                    try:
                        self.mongo[MONGO_COLLECTION_PRODUCTS].insert_one(item)
                    except Exception as e:
                        pass

            
            # Extract next page token
            next_page_token = data.get("nextPageToken")
            
            if not next_page_token:
                logging.info(f"[{meta['city']}] No nextPageToken found, reached last page.")
                return False
            
            # Update pageToken for next request
            json_data["pageToken"] = next_page_token
            return True
        
        logging.warning(f"[{meta['city']}] No products found")
        return False
    
    def close(self):
        """Close function for all module object closing"""
        self.mongo_client.close()
   


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()