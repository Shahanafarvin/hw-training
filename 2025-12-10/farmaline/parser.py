import requests
from pymongo import MongoClient
from parsel import Selector
from settings import logging,MONGO_DB,MONGO_COLLECTION_PRODUCTS,MONGO_COLLECTION_URL_FAILED,MONGO_COLLECTION_DATA

class Parser:
    """Parser for Farmaline Product Details"""
    
    def __init__(self):
        self.mongo = MongoClient("mongodb://localhost:27017/")
        self.db = self.mongo[MONGO_DB]
   
    
    def start(self):
        """start code"""
        
        for doc in list(self.db[MONGO_COLLECTION_PRODUCTS].find()):
            url = doc.get("product_url")
            
            logging.info(f"Fetching: {url}")
            
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    self.parse_item(url, response, doc)
                else:
                    logging.warning(f"Failed: {response.status_code}")
                    self.db[MONGO_COLLECTION_URL_FAILED].insert_one({"url":url, 'status_code': response.status_code})
            except Exception as e:
                logging.error(f"Request error for {url}: {e}")
                self.db[MONGO_COLLECTION_URL_FAILED].insert_one({"url":url, 'error': e})
                
    def close(self):
        """connection close"""
        self.mongo.close()
    
    def parse_item(self, url, response, doc):
        """item part"""
        sel = Selector(text=response.text)
        
        # XPATH
        BREADCRUMBS_XPATH = "//span[@class='hidden items-center gap-2 whitespace-nowrap first:flex mobile-sm:last:flex desktop:flex desktop:last:hidden']//text()"
        REVIEWS_XPATH = "//a[@data-qa-id='number-of-ratings-text']/text()"
        PACKAGE_SIZE_XPATH = "//div[@data-qa-id='product-attribute-package_size']//text()"
        PRICE_PER_SIZE_XPATH = "//div[@class='text-xs text-dark-primary-strong']//text()"
        DETAILS_ITEMS_XPATH = "//li[contains(@class,'flex grow flex-row items-start text-s text-dark-primary-max')]"
        DETAILS_KEY_XPATH = ".//dt//text()"
        DETAILS_VALUE_XPATH = ".//dd//text()"
        PRODUCT_DESCRIPTION_XPATH = "//div[@data-qa-id='product-description']//text()"
        RATING_XPATH = "//div[@data-qa-id='product-ratings-container']//span[@class='mb-2.5 text-4xl']//text()"
        IMAGES_XPATH = "//button[contains(@class,'w-1/3')]//picture//img/@src"
        
        # EXTRACT
        breadcrumbs_list = sel.xpath(BREADCRUMBS_XPATH).getall()
        reviews = sel.xpath(REVIEWS_XPATH).get()
        package_size = "".join(sel.xpath(PACKAGE_SIZE_XPATH).getall())
        price_per_size = sel.xpath(PRICE_PER_SIZE_XPATH).get()
        details_items = sel.xpath(DETAILS_ITEMS_XPATH)
        product_description_list = sel.xpath(PRODUCT_DESCRIPTION_XPATH).getall()
        rating = sel.xpath(RATING_XPATH).get()
        images_list = sel.xpath(IMAGES_XPATH).getall()
        
        # CLEAN
        breadcrumbs = " > ".join(breadcrumbs_list) if breadcrumbs_list else ""
        
        details_dict = {}
        for item in details_items:
            key = item.xpath(DETAILS_KEY_XPATH).get()
            value = item.xpath(DETAILS_VALUE_XPATH).get()
            if key and value:
                details_dict[key.strip()] = value.strip()
        details=", ".join(f"{k}: {v}" for k, v in details_dict.items())

        product_description = " ".join(
            [d.strip() for d in product_description_list if d.strip()]
        ) if product_description_list else ""
        
        images = ",".join(images_list) if images_list else ""
        
        # ITEM YIELD
        item = {}
        item["product_url"] = url
        item["breadcrumbs"] = breadcrumbs
        item["product_name"] = doc.get("product_name")
        item["selling_price"] = doc.get("selling_price")
        item["discount"] = doc.get("discount")
        item["regular_price"] = doc.get("regular_price")
        item["reviews"] = reviews
        item["package_size"] = package_size
        item["price_per_size"] = price_per_size
        item["details"] = details
        item["product_description"] = product_description
        item["rating"] = rating
        item["images"] = images
        item["match_type"] = doc.get("match_type")
        item["ean"] = doc.get("ean")
        item["cnk"] = doc.get("cnk")
        item["score"] = doc.get("score")
        
        logging.info(item)
        
        try:
            self.db[MONGO_COLLECTION_DATA].insert_one(item)
            logging.info(" Saved product details")
        except Exception as e:
            pass


if __name__ == "__main__":
    parser_obj = Parser()
    parser_obj.start()
    parser_obj.close()