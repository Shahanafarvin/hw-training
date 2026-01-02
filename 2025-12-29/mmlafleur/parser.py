import logging
import requests
from parsel import Selector
from html import unescape
import re
from pymongo import MongoClient
from settings import MONGO_DB, MONGO_COLLECTION_PRODUCTS, MONGO_COLLECTION_DATA,MONGO_COLLECTION_URL_FAILED


class Parser:
    """Parser for product details"""
    
    def __init__(self):
        self.mongo_client = MongoClient('mongodb://localhost:27017/')
        self.mongo = self.mongo_client[MONGO_DB]
        
    def start(self):
        """start code"""
        
        metas = self.mongo[MONGO_COLLECTION_PRODUCTS].find({})
        
        for meta in metas:
            url = meta.get('product_url')
            product_sku = meta.get('product_sku', '')
            category = meta.get('category', '')
            description = meta.get('description', '')
            
            if not url:
                continue
                
            logging.info(f"Fetching: {url}")
            
            try:
                response = requests.get(url)
                if response and response.status_code == 200:
                    self.parse_item(url, response, product_sku, category, description)
                else:
                    self.mongo[MONGO_COLLECTION_URL_FAILED]._insert_one({'url': url, 'status_code': response.status_code})
            except Exception as e:
                logging.error(f"Request failed for {url}: {e}")
                
    def close(self):
        """connection close"""
        self.mongo.close()
      
    def clean_text_list(self, raw):
        """Clean text data"""
        if not raw:
            return ""
        
        # Decode HTML entities
        raw = unescape(raw)
        
        # Remove HTML tags if any slipped in
        raw = re.sub(r"<[^>]+>", " ", raw)
        
        # Replace newlines, tabs with space
        raw = re.sub(r"[\n\r\t]+", " ", raw)
        
        # Remove repeated commas / spaces
        raw = re.sub(r"\s*,\s*", ",", raw)
        raw = re.sub(r"(,\s*)+", ", ", raw)
        
        # Strip leading/trailing commas and spaces
        raw = raw.strip(" ,")
        
        return raw
        
    def parse_item(self, url, response, product_sku, category, description):
        """item part"""
        sel = Selector(text=response.text)
        
        # XPATH
        PRODUCT_NAME_XPATH = "//h1[@class='ProductMeta__Title Heading h2 h2--alt']/text()"
        ORIGINAL_PRICE_XPATH = "//span[@class='ProductMeta__Price Price']/text()"
        SALE_PRICE_XPATH = "//span[@class='ProductMeta__Price Price Price--highlight']/text()"
        COMPARE_PRICE_XPATH = "//span[@class='ProductMeta__Price Price Price--compareAt']/text()"
        NO_OF_REVIEWS_XPATH = "//div[@class='loox-rating']/@data-raters"
        RATING_XPATH = "//div[@class='loox-rating']/@data-rating"
        FEATURES_XPATH = "//div[@class='Rte product-attributes']//text()"
        COLOR_XPATH = "//span[@id='productSwatchSelected']/text()"
        SIZE_XPATH = "//ul[@class='SizeSwatchList HorizontalList HorizontalList--spacingExtraTight']/li//text()"
        
        # EXTRACT
        product_name = sel.xpath(PRODUCT_NAME_XPATH).get()
        original_price = sel.xpath(ORIGINAL_PRICE_XPATH).get()
        sale_price = original_price
        no_of_reviews = sel.xpath(NO_OF_REVIEWS_XPATH).get()
        rating = sel.xpath(RATING_XPATH).get()
        features = sel.xpath(FEATURES_XPATH).getall()
        color = sel.xpath(COLOR_XPATH).get()
        size = sel.xpath(SIZE_XPATH).getall()
        
        # Handle sale price logic
        if not original_price:
            sale_price = sel.xpath(SALE_PRICE_XPATH).get()
            original_price = sel.xpath(COMPARE_PRICE_XPATH).get()
        
        # CLEAN
        product_name = product_name.strip() if product_name else ""
        brand = "MM.LaFleur"
        currency = "USD"
        original_price = original_price.replace("$", "").strip() if original_price else ""
        sale_price = sale_price.replace("$", "").strip() if sale_price else ""
        features = ", ".join(features).strip() if features else ""
        color = color.strip() if color else ""
        size = ", ".join(size) if size else ""
        
        # Clean text using clean_text_list
        features = self.clean_text_list(features)
        color = self.clean_text_list(color)
        size = self.clean_text_list(size)
        description = self.clean_text_list(description)
        
        # ITEM YIELD
        item = {}
        item["website"] = "MM.LaFleur"
        item["url"] = url
        item["product_sku"] = product_sku
        item["product_name"] = product_name
        item["brand"] = brand
        item["currency"] = currency
        item["original_price"] = original_price
        item["sale_price"] = sale_price
        item["category"] = category
        item["no_of_reviews"] = no_of_reviews
        item["rating"] = rating
        item["description"] = description
        item["features"] = features
        item["color"] = color
        item["size"] = size
        
        logging.info(item)
        
        try:
            self.mongo[MONGO_COLLECTION_DATA].insert_one(item)
        except Exception as e:
            logging.error(f"Failed to insert item: {e}")
            pass


if __name__ == "__main__":
    parser_obj = Parser()
    parser_obj.start()
    parser_obj.close()