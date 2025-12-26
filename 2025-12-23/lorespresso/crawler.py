import requests
from pymongo import MongoClient
from settings import MONGO_DB, MONGO_COLLECTION_PRODUCTS, MONGO_COLLECTION_CATEGORY, BASE_URL, logging, headers

class Crawler:
    """Crawling Products from Lorespresso"""
    
    def __init__(self):
        """Initialize MongoDB connection"""
        self.mongo_client = MongoClient('mongodb://localhost:27017/')
        self.mongo = self.mongo_client[MONGO_DB]
        self.mongo[MONGO_COLLECTION_PRODUCTS].create_index("product_url",unique=True)
        
    def start(self):
        """Requesting Start url"""
        
        # Fetch categories from MongoDB
        categories = self.mongo[MONGO_COLLECTION_CATEGORY].find({})
        category_list = list(categories)
        
        if not category_list:
            logging.warning("No categories found in database")
            return
        
        logging.info(f"Found {len(category_list)} categories to crawl")
        
        for category_doc in category_list[:5]:  #last two categories avoided
            category_name = category_doc.get('category_name')
            category_url = category_doc.get('category_url')
            
            if not category_name:
                logging.warning(f"Skipping category with missing name")
                continue
            
            meta = {}
            meta['category_name'] = category_name
            meta['category_url'] = category_url
            
            # Generate API URL
            api_url = f"https://www.lorespresso.com/_next/data/liEcZFYMRVmiiJWDSN8Yr/en_gb/{category_name}.json?url={category_name}"
            
            headers['Referer'] = f"https://www.lorespresso.com/en_gb/{category_name}"
            
            try:
                response = requests.get(api_url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    self.parse_item(response, meta)
                else:
                    logging.error(f"Failed to retrieve data for category: {category_name}, Status Code: {response.status_code}")
    
                    
            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed for category {category_name}: {e}")
    
    def parse_item(self, response, meta):
        """Parse products from API response"""
        try:
            data = response.json()
            logging.info(f"Parsing products for category: {meta.get('category_name')}")
            
            # Extract products safely
            products_data = data.get("pageProps", {}).get("products", {})
            
            if not products_data:
                logging.warning(f"No products data found for category: {meta.get('category_name')}")
                return
            
            if "product_ranges" in products_data:
                products_categories = products_data["product_ranges"]
            else:
                products_categories = [products_data]  # wrap in list for uniform iteration
            
            
            for pcat in products_categories:
                # Some categories use nested structure, some are flat
                products = (
                    pcat.get("category", {}).get("products", {}).get("items", []) or
                    pcat.get("items", [])
                )
                
                for product in products:
                    name = product.get("name")
                    sku = product.get("sku")
                    product_url = f"https://www.lorespresso.com/en_gb/p/{product.get('url_key')}"
                    rating = product.get("rating_summary")
                    review = product.get("review_count")
                    price_range = product.get("price_range")

                    # ITEM YIELD
                    item = {}
                    item['name'] = name
                    item['sku'] = sku
                    item['product_url'] = product_url
                    item['rating'] = rating
                    item['review_count'] = review
                    item['price_range'] = price_range
                    
                    logging.info(item)
                    
                    try:
                        self.mongo[MONGO_COLLECTION_PRODUCTS].insert_one(item)
                    except Exception as e:
                        logging.error(f"Failed to save product {item.get('sku')}: {e}")
            
        except Exception as e:
            logging.error(f"Error parsing products for category {meta.get('category_name')}: {e}")
    
    def close(self):
        """Close function for all module object closing"""
        self.mongo_client.close()


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()