import requests
from pymongo import MongoClient
from parsel import Selector
from fuzzywuzzy import fuzz
from urllib.parse import quote_plus
from settings import logging,MONGO_DB,MONGO_COLLECTION_INPUT,MONGO_COLLECTION_PRODUCTS,BASE_URL


class Crawler:
    """Crawling Farmaline Products"""
    
    def __init__(self):
        self.mongo = MongoClient("mongodb://localhost:27017/")
        self.db = self.mongo["farmaline_db"]
        
    
    def start(self):
        """Processing input items"""
        for item in list(self.db[MONGO_COLLECTION_INPUT].find()):
            ean = str(item.get("EAN MASTER", "")).strip()
            cnk = str(item.get("CNK BELUX", "")).strip()
            input_name = str(item.get("PRODUCT GENERAL NAME", "")).strip()
            
            logging.info(f"Processing: {input_name}")
            
            meta = {
                'ean': ean,
                'cnk': cnk,
                'input_name': input_name,
                'product_saved': False
            }
            
            # Try EAN search first
            if ean and not meta['product_saved']:
                q = quote_plus(ean)
                url = f"https://www.farmaline.be/nl/search.htm?eventName=search-submit&i=1&q={q}&searchChannel=algolia"
                
                response = requests.get(url)
                if response.status_code == 200:
                    self.parse_item(response, meta, ean, "EAN")
                    
            # Try CNK search if not saved
            if cnk and not meta['product_saved']:
                q = quote_plus(cnk)
                url = f"https://www.farmaline.be/nl/search.htm?eventName=search-submit&i=1&q={q}&searchChannel=algolia"
                
                response = requests.get(url)
                if response.status_code == 200:
                    self.parse_item(response, meta, cnk, "CNK")
                    
            # Try product name search if not saved
            if input_name and not meta['product_saved']:
                q = quote_plus(input_name)
                url = f"https://www.farmaline.be/nl/search.htm?eventName=search-submit&i=1&q={q}&searchChannel=algolia"
                
                response = requests.get(url)
                if response.status_code == 200:
                    self.parse_item(response, meta, input_name, "NAME")
            
 
    
    def parse_item(self, response, meta, search_term, search_type):
        """Parse product listings"""
        sel = Selector(response.text)
        
        # XPATH
        PRODUCT_XPATH = "//li[@data-qa-id='result-list-entry']"
        URL_XPATH =".//a[@data-qa-id='serp-result-item-title']/@href"
        NAME_XPATH = ".//a[@data-qa-id='serp-result-item-title']//text()"
        PRICE_XPATH = ".//span[@data-qa-id='entry-price']//text()"
        DISCOUNT_XPATH = ".//div[@class='flex min-w-12 items-center justify-center p-1 text-dark-primary-max rounded-full bg-light-tertiary font-mono text-xs font-medium']/span/text()"
        REGULAR_PRICE_XPATH = ".//div[@class='text-dark-primary-max']/span[@class='line-through']/text()"
        CARD_TEXT_XPATH = ".//text()"
        
        # EXTRACT
        products = sel.xpath(PRODUCT_XPATH)
        
        
        if search_type in ["EAN", "CNK"]:
            if len(products) == 1:
                p = products[0]
                product_url = f"{BASE_URL}{p.xpath(URL_XPATH).get()}"
                name = p.xpath(NAME_XPATH).get()
                selling_price = "".join(p.xpath(PRICE_XPATH).getall())
                discount = p.xpath(DISCOUNT_XPATH).get()
                regular_price = p.xpath(REGULAR_PRICE_XPATH).get()
                match_type = f"{search_type} EXACT"
                
                item={}
                item["product_url"]=product_url
                item["product_name"]=name
                item["selling_price"]=selling_price
                item["discount"]=discount
                item["regular_price"]=regular_price
                item["match_type"]=match_type
                item[f"{search_type.lower()}"]= search_term

                logging.info(item)
                try:
                    self.db[MONGO_COLLECTION_PRODUCTS].insert_one(item)
                    logging.info(f" Saved via single {search_type} result")
                    meta['product_saved'] = True
                except:
                    pass

            
            elif len(products) > 1:
                matched = []
                
                for p in products:

                    card_text = " ".join(p.xpath(CARD_TEXT_XPATH).getall()).upper()
                    
                    if search_term in card_text:
                        product_url = f"{BASE_URL}{p.xpath(URL_XPATH).get()}"
                        name = p.xpath(NAME_XPATH).get()
                        selling_price = "".join(p.xpath(PRICE_XPATH).getall())
                        discount = p.xpath(DISCOUNT_XPATH).get()
                        regular_price = p.xpath(REGULAR_PRICE_XPATH).get()
                        match_type = f"{search_type} IN CARD"
                        
                        item={}
                        item["product_url"]=product_url
                        item["product_name"]=name
                        item["selling_price"]=selling_price
                        item["discount"]=discount
                        item["regular_price"]=regular_price
                        item["match_type"]=match_type
                        item[f"{search_type.lower()}"]= search_term
                        matched.append(item)
                
                if len(matched) == 1:
                    logging.info(matched[0])
                    try:
                        self.db[MONGO_COLLECTION_PRODUCTS].insert_one(matched[0])
                        logging.info(f"✔ Saved via {search_type} found in exactly one card")
                        meta['product_saved'] = True
                    except:
                        pass
                else:
                    logging.warning(f"{search_type} not uniquely identifiable in PLP")

        elif search_type == "NAME":
            exact = None
            partial = []
            
            for p in products:
                product_url = f"{BASE_URL}{p.xpath(URL_XPATH).get()}"
                name = p.xpath(NAME_XPATH).get()
                selling_price = "".join(p.xpath(PRICE_XPATH).getall())
                discount = p.xpath(DISCOUNT_XPATH).get()
                regular_price = p.xpath(REGULAR_PRICE_XPATH).get()
                
                if not name or not product_url or "api" in product_url:
                    continue
                
                
                score = fuzz.token_sort_ratio(search_term.upper(), name.upper())

                item={}
                item["product_url"]=product_url
                item["product_name"]=name
                item["selling_price"]=selling_price
                item["discount"]=discount
                item["regular_price"]=regular_price
                
                if score == 100:
                    item['match_type'] = "NAME EXACT"
                    item['score'] = score
                    exact = item
                    break
                elif 70 <= score < 100:
                    item['match_type'] = "NAME PARTIAL"
                    item['score'] = score
                    partial.append(item)

           

            if exact:
                logging.info(exact)
                try:
                    self.db[MONGO_COLLECTION_PRODUCTS].insert_one(exact)
                    logging.info(" Saved exact name match")
                except: 
                    pass
                    
            elif partial:
                logging.info(partial)
                try:
                    self.db[MONGO_COLLECTION_PRODUCTS].insert_many(partial)
                    logging.info(f" Saved {len(partial)} partial name matches")
                except:
                    pass
                    
            else:
                logging.warning(" No name match found")
    
    def close(self):
        """Close function for all module object closing"""
        self.mongo.close()
       

if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()