import requests
from mongoengine import connect
from parsel import Selector
from items import ProductCategoryItem
from settings import logging, MONGO_DB, MONGO_HOST, MONGO_PORT

class Crawler:
    """Crawling Urls"""
    def __init__(self):
        self.mongo = connect(db=MONGO_DB, host=MONGO_HOST, alias="default", port=MONGO_PORT)
    
    def start(self):
        """Requesting Start url"""
        url = 'https://www.halfords.com/'
        
        meta = {}
        meta['url'] = url
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                self.parse_item(response, meta)
            else:
                logging.warning(f"Status code {response.status_code} for {url}")
        except Exception as e:
            logging.error(f"Error fetching {url}: {str(e)}")
            

    def parse_item(self, response, meta):
        """item part"""
        sel = Selector(response.text)
        
        #XPATH
        CATEGORYTAG_XPATH="//li[@class='mm-list-list-item mm-list-list-item1  ']"
        SUBCATEGORYTAG_XPATH=".//li[@class='mm-list-list-item mm-list-list-item2  ']"   
        SUBSUBCATEGORYTAG_XPATH=".//li[@class='mm-list-list-item mm-list-list-item3  ']"   
        NAME_XPATH="./a//text()"
        URL_XPATH="./a/@href"

        #EXTRACT
        categories = {}
        category_tags = sel.xpath(CATEGORYTAG_XPATH)
        
        for li in category_tags:
            # Category Name & URL
            name = li.xpath(NAME_XPATH).get()
            link = li.xpath(URL_XPATH).get()
            if not link:
                continue
            full_link = f"https://www.halfords.com{link}"
            
            categories[name] = {
                "url": full_link,
                "subcategories": {}
            }
            
            # SUB-CATEGORIES
            subcategory_tags = li.xpath(SUBCATEGORYTAG_XPATH)
            
            for sub_li in subcategory_tags:
                sub_name = sub_li.xpath(NAME_XPATH).get()
                sub_link = sub_li.xpath(URL_XPATH).get()
                if not sub_link:
                    continue
                full_sublink = f"https://www.halfords.com{sub_link}"
                
                categories[name]["subcategories"][sub_name] = {
                    "url": full_sublink,
                    "sub_subcategories": {}
                }
                
                # SUB-SUB-CATEGORIES
                sub_subcategory_tags = sub_li.xpath(SUBSUBCATEGORYTAG_XPATH)
                
                for sub_subli in sub_subcategory_tags:
                    sub_sub_name = sub_subli.xpath(NAME_XPATH).get()
                    sub_sub_link = sub_subli.xpath(URL_XPATH).get()
                    if not sub_sub_link:
                        continue
                    full_sub_sublink = f"https://www.halfords.com{sub_sub_link}"
                    
                    categories[name]["subcategories"][sub_name]["sub_subcategories"][sub_sub_name] = {
                        "url": full_sub_sublink
                    }
        
        # ITEM YIELD
        item = {}
        item["categories"]= categories
        
        logging.info(item)
        
        try:
            ProductCategoryItem(**item).save()
            logging.info("Categories saved to MongoDB")
        except Exception as e:
            logging.error(f"Error saving to MongoDB: {str(e)}")
    
    def close(self):
        """Close function for all module object closing"""
        self.mongo.close()
        


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()