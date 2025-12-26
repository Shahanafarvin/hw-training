import requests
from parsel import Selector
from pymongo import MongoClient
from settings import MONGO_DB, MONGO_COLLECTION_CATEGORY, BASE_URL, logging

class CategoryCrawler:
    """Extract categories from Lorespresso website"""
    
    def __init__(self):
        """Initialize MongoDB connection"""
        
        self.mongo_client = MongoClient('mongodb://localhost:27017/')
        self.mongo = self.mongo_client[MONGO_DB]
        
    
    def start(self):
        """Request start URL and extract categories"""
        try:
            response = requests.get(BASE_URL)
            logging.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                self.parse_item(response)
            else:
                logging.error(f"Failed to fetch URL. Status code: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
    
    def parse_item(self, response):
        """Parse and extract category URLs"""
        sel = Selector(text=response.text)
        
        # XPath for category links
        CATEGORY_XPATH = "//a[@class='MuiTypography-root MuiTypography-inherit MuiLink-root MuiLink-underlineAlways mui-style-1wlgmvd']/@href"
        
        # Extract all category URLs
        categories = sel.xpath(CATEGORY_XPATH).getall()
        
        logging.info(f"Found {len(categories)} categories")
        
        if categories:
            for category_url in categories:
                # Split URL and extract category name from last part
                url_parts = category_url.strip('/').split('/')
                category_name = url_parts[-1] if url_parts else "unknown"
                
                # ITEM YIELD
                item = {}
                item['category_name'] = category_name
                item['category_url'] = f"https://www.lorespresso.com{category_url}"
                logging.info(item)
                
                
                try:
                    self.mongo[MONGO_COLLECTION_CATEGORY].insert_one(item)
                    logging.info(f"Inserted category: {category_name}")
                except Exception as e:
                    logging.error(f"Failed to insert category {category_name}: {e}")
        else:
            logging.warning("No categories found")
    
    def close(self):
        """Close MongoDB connection"""
        self.mongo_client.close()
       

if __name__ == "__main__":
    extractor = CategoryCrawler()
    extractor.start()
    extractor.close()