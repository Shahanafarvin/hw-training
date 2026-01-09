import requests
import math
from pymongo import MongoClient
from settings import MONGO_DB,MONGO_COLLECTION_CATEGORY,MONGO_COLLECTION_PRODUCTS
import logging

class Crawler:
    """Crawling Product URLs"""
    
    def __init__(self):
        self.mongo_client = MongoClient('mongodb://mongotraining:a4892e52373844dc4862e6c468d11b6df7938e16@167.172.244.21:27017/?authSource=admin')
        self.mongo = self.mongo_client[MONGO_DB]
        self.mongo[MONGO_COLLECTION_PRODUCTS].create_index("product_url",unique=True)
        self.PAGE_SIZE = 24
        
    def start(self):
        """Requesting Start url"""
        
        categories = self.mongo[MONGO_COLLECTION_CATEGORY].find({})
        
        for category_doc in categories:
            category_key = category_doc.get('category_key')
            category_name = category_doc.get('category_name')
            
            if not category_key:
                continue
                
            meta = {}
            meta['category'] = category_name
            meta['category_key'] = category_key
            
            
            api_url = f"https://mmlafleur.com/collections/{category_key}?view=ajax"
            print(api_url)
            page = meta.get("page", 1)  # initialising page for pagination
            page_api_url = f"{api_url}&page={page}"
            
            while True:
                response = requests.get(page_api_url)
                logging.info(response.headers.get("Content-Type"))
                if response.status_code == 200:
                    is_next = self.parse_item(response, meta)
                    if not is_next:
                        logging.info("Pagination completed")
                        break
                    
                    # pagination crawling
                    page += 1
                    page_api_url = f"{api_url}&page={page}"
                    meta["page"] = page
                else:
                    logging.error(f"Failed to fetch page {page}, Status: {response.status_code}")
                    break
                    
    def parse_item(self, response, meta):
        """Product extraction part"""
        
        data = response.json()
       
        
        # Get total products from first page response
        if meta.get("page", 1) == 1:
            total_products = data[0].get("total") if data else 0
            if total_products:
                total_pages = math.ceil(total_products / self.PAGE_SIZE)
                meta['total_pages'] = total_pages
                meta['total_products'] = total_products
                logging.info(f"Total products: {total_products}, Total pages: {total_pages}")
        
        # EXTRACT products
        products = data if isinstance(data, list) else []
        
        if products:
            for product_data in products:
                product_info = product_data.get("product", {})
                
                handle = product_info.get("handle", "")
                description = product_info.get("description", "")
                sku = product_info.get("id", "")
                
                if not handle:
                    continue
                
                product_url = f"https://mmlafleur.com/products/{handle}"
                
                # ITEM YIELD
                item = {}
                item['product_url'] = product_url
                item['description'] = description
                item['product_sku'] = sku
                item['category'] = meta.get('category')
               
                
                logging.info(item)
                
                try:
                    self.mongo[MONGO_COLLECTION_PRODUCTS].insert_one(item)
                except Exception as e:
                    logging.error(f"Failed to insert product: {e}")
                    pass
            
            # Check if there are more pages
            current_page = meta.get("page", 1)
            total_pages = meta.get("total_pages", 1)
            
            if current_page < total_pages:
                return True
            else:
                return False
        
        logging.warning("No products found")
        return False
        
    def close(self):
        """Close function for all module object closing"""
        self.mongo_client.close()
   


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()