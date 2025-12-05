from curl_cffi import requests
from parsel import Selector
from pymongo import MongoClient
from settings import logging, BASE_URL, MONGO_DB, MONGO_COLLECTION_CATEGORY


class Crawler:
    """Crawling Category URLs from Max Fashion"""
    
    def __init__(self):
        self.client = MongoClient("localhost", 27017)
        self.mongo = self.client[MONGO_DB]

        
    def start(self):
        """Requesting Start url"""
       
        url='https://www.maxfashion.com/ae/en/'

        meta = {}
        meta['url'] = url
        
        response = requests.get(url, impersonate="chrome")
        
        if response.status_code == 200:
            self.parse_item(response, meta)
        
        
    def parse_item(self, response, meta):
        """Parse category structure"""
        sel = Selector(response.text)
        
        # XPATH
        CATEGORIES_XPATH = '//div[contains(@class,"jss101 departments")]'
        CATEGORY_NAME_XPATH = './a//text()'
        CATEGORY_URL_XPATH = './a/@href'
        SUBCATEGORIES_XPATH = './/div[contains(@class,"jss117 category")]'
        SUBCAT_NAME_XPATH = './/a//text()'
        SUBCAT_URL_XPATH = './/a/@href'
        SUBSUBCATEGORIES_XPATH = './/div[@class="jss133"]'
        SUBSUB_NAME_XPATH = './a/text()'
        SUBSUB_URL_XPATH = './a/@href'
        
        # EXTRACT
        categories = sel.xpath(CATEGORIES_XPATH)
        
        if categories:
            for category in categories:
                category_name = category.xpath(CATEGORY_NAME_XPATH).get()
                category_url_path = category.xpath(CATEGORY_URL_XPATH).get()
                
                if not category_name or not category_url_path:
                    continue
                
                category_url = f"{BASE_URL}{category_url_path}"

                subcategories = category.xpath(SUBCATEGORIES_XPATH)
                subcategory_list=[]
                for subcat in subcategories:
                    subcategory_name = subcat.xpath(SUBCAT_NAME_XPATH).get()
                    subcategory_url_path = subcat.xpath(SUBCAT_URL_XPATH).get()
                    
                    if not subcategory_name or not subcategory_url_path:
                        continue
                    
                    subcategory_url = f"{BASE_URL}{subcategory_url_path}"
                    
                    subcategory_item = {}
                    subcategory_item['name'] = subcategory_name.strip()
                    subcategory_item['url'] = subcategory_url
                    subcategory_item['subsubcategories'] = []
                    
                    subsubcats = subcat.xpath(SUBSUBCATEGORIES_XPATH)
                    
                    for subsub in subsubcats:
                        subsubcategory_name = subsub.xpath(SUBSUB_NAME_XPATH).get()
                        subsubcategory_url_path = subsub.xpath(SUBSUB_URL_XPATH).get()
                        
                        if not subsubcategory_name or not subsubcategory_url_path:
                            continue
                        
                        subsubcategory_url = f"{BASE_URL}{subsubcategory_url_path}"
                        
                        subsubcategory_item = {}
                        subsubcategory_item['name'] = subsubcategory_name.strip()
                        subsubcategory_item['url'] = subsubcategory_url
                        
                        subcategory_item['subsubcategories'].append(subsubcategory_item)

                    subcategory_list.append(subcategory_item)

                # ITEM YIELD
                item = {}
                item['name'] = category_name.strip()
                item['url'] = category_url
                item['subcategories'] =subcategory_list
                
                logging.info(item)
                
                try:
                    self.mongo[MONGO_COLLECTION_CATEGORY].insert_one(item)
                except:
                    pass
            
            return True
        
        return False
    
    def close(self):
        """Close function for all module object closing"""
        self.client.close()
      

if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()