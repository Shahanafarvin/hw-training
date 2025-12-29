import time
import random
import math
import requests
from pymongo import MongoClient
from settings import logging, BASE_URL, PAGE_SIZE, MAX_RETRIES, headers, MONGO_DB ,MONGO_COLLECTION_PRODUCTS

class Crawler:
    """Crawling 3M Products"""
    
    def __init__(self):
        # MongoDB connection
        self.mongo = MongoClient('mongodb://localhost:27017/')
        self.db = self.mongo[MONGO_DB]
    
    def start(self):
        """Requesting Start url"""

        meta = {}
        meta['page'] = 0
        meta['total_pages'] = None
        
        # First request to get total pages
        params = {"size": PAGE_SIZE, "start": 0}
        response = requests.get(BASE_URL, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        total_products = data.get("total", 0)
        meta['total_pages'] = math.ceil(total_products / PAGE_SIZE)
        logging.info(f"Total products: {total_products}, Total pages: {meta['total_pages']}")
        
        # Parse first page
        self.parse_item(response, meta)
        
        # Pagination crawling
        while meta['page'] < meta['total_pages'] - 1:
            meta['page'] += 1
            page = meta['page']
            start = page * PAGE_SIZE
            params = {"size": PAGE_SIZE, "start": start}
            
            retries = 0
            while retries < MAX_RETRIES:
                time.sleep(random.uniform(2, 4))
                
                response = requests.get(BASE_URL, params=params, headers=headers)
                
                if response.status_code == 404:
                    logging.info(f"End of products at page={page}")
                    meta['page'] = meta['total_pages']
                    break
                
                if response.status_code in (429, 503):
                    retries += 1
                    logging.warning(f"Server busy ({response.status_code}), retry {retries}/{MAX_RETRIES}")
                    time.sleep(5 * retries)
                    continue
                
                response.raise_for_status()
                break
            else:
                logging.warning(f"Skipping page={page} after {MAX_RETRIES} retries")
                continue
            
            is_next = self.parse_item(response, meta)
            if not is_next:
                logging.info("No more products found")
                break
        
        logging.info("Pagination completed")
    
    def parse_item(self, response, meta):
        """item part"""
        
        data = response.json()
    
        products = data.get("items", [])
        
        if products:
            for product in products:
                item = {}
                item['name'] = product.get("name")
                item['productNumber'] = product.get("productNumber")
                item['stockNumber'] = product.get("stockNumber")
                item['upc'] = product.get("upc")
                item['url'] = product.get("url")
               
                
                logging.info(item)
                
                try:
                    self.db[MONGO_COLLECTION_PRODUCTS].insert_one(item)
                except:
                    pass
            
            return True
        
        return False
    
    def close(self):
        """Close function for all module object closing"""
        self.mongo.close()
      
if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()