import logging
import requests
from parsel import Selector
from pymongo import MongoClient
from settings import (
    MONGO_DB,
    MONGO_COLLECTION_CATEGORY,
    BASE_URL
)

class CategoryCrawler:
    """Crawling Category URLs"""
    
    def __init__(self):
        self.mongo_client = MongoClient('mongodb://mongotraining:a4892e52373844dc4862e6c468d11b6df7938e16@167.172.244.21:27017/?authSource=admin')
        self.mongo = self.mongo_client[MONGO_DB]
        
    def start(self):
        """Requesting Start url"""
        
        meta = {}
        meta['main_url'] = BASE_URL
        
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            self.parse_item(response, meta)
        else:
            logging.error(f"Failed to fetch {BASE_URL}, Status: {response.status_code}")
            
    def parse_item(self, response, meta):
        """Category extraction part"""
        sel = Selector(response.text)
        
        # XPATH
        CATEGORY_XPATH = '//div[@class="MegaMenu__Item MegaMenu__Item--fit"][1]//li'
        URL_XPATH = './/a/@href'
        NAME_XPATH = './/a/text()'
        
        # EXTRACT
        categories = sel.xpath(CATEGORY_XPATH)
        
        if categories:
            for cat in categories[:10]:
                category_url = cat.xpath(URL_XPATH).get()
                category_name = cat.xpath(NAME_XPATH).get()
                
                if category_url and category_name:
                    # Handle relative URLs
                    if not category_url.startswith("http"):
                        category_url = f"https://mmlafleur.com{category_url}"
                    
                    category_key=self.parse_category(category_url)
                    # ITEM YIELD
                    item = {}
                    item['category_url'] = category_url
                    item['category_name'] = category_name.strip()
                    item['category_key']=category_key
                    
                    logging.info(item)
                    
                    try:
                        self.mongo[MONGO_COLLECTION_CATEGORY].insert_one(item)
                    except Exception as e:
                        logging.error(f"Failed to insert category: {e}")
                        pass
            
            return True
        
        return False
        
    def parse_category(self,url):
        """Visit each category URL and extract category key"""
        
        CATEGORY_KEY_XPATH = '//product-list/@list'
        
        response=requests.get(url)
        sel=Selector(response.text)

        category_key=sel.xpath(CATEGORY_KEY_XPATH).get()
        
        return category_key
    
    def close(self):
        """Close function for all module object closing"""
        self.mongo_client.close()
        


if __name__ == "__main__":
    crawler = CategoryCrawler()
    crawler.start()
    crawler.close()