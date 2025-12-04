import logging
import requests
import time
from datetime import datetime
from parsel import Selector
from pymongo import MongoClient
from settings import HEADERS, MONGO_DB, MONGO_COLLECTION_URLS, MONGO_COLLECTION_DATA, MONGO_COLLECTION_URL_FAILED, proxies
#from items import ProductUrlItem, ProductDataItem


class Parser:
    """parser"""

    def __init__(self):
        self.client = MongoClient("localhost", 27017)
        self.mongo = self.client[MONGO_DB]

    def start(self):
        """start code"""
        # Fetch URLs from MongoDB collection
        metas = []
        for doc in self.mongo[MONGO_COLLECTION_URLS].find():
            metas.append({'product': doc})
        
        
        for meta in metas:
            time.sleep(1)
            url = meta.get('product', {}).get('url')
            response = requests.get(url, headers=HEADERS, proxies=proxies)
            if response.status_code == 200:
                self.parse_item(response, meta)
            else:
                logging.error(f"Failed to fetch URL: {url} with status code {response.status_code}")
                try:
                    self.mongo[MONGO_COLLECTION_URL_FAILED].insert_one({'url': url, 'status_code': response.status_code})
                except:
                    pass    

           
    def close(self):
        """connection close"""

        self.client.close()

    def parse_item(self, response, meta):
        """item part"""

        sel = Selector(text=response.text)

        # XPATH
        LOCATION_XPATH = "//h2[@itemprop='address']//text()"
        PRICE_XPATH= "//div[@class='price-data']/p[@class='headline-1 price']/text()"
        MAXPRICE_XPATH = "//div[@class='price-data max-price']//p[@class='headline-1 price']/text()"
        DETAILS_XPATH = "//div[@class='header']//div[2]//text()"
        TABLEDATA_XPATH="//div[@class='rowData']"
        KEY_XPATH= "./div[1]/text()"
        VALUE_XPATH= "./div[2]//text() | ./a[1]//text()"

        # EXTRACT
        location = sel.xpath(LOCATION_XPATH).get()
        scraped_ts = datetime.now().strftime("%Y-%m-%d")
        price=sel.xpath(PRICE_XPATH).get()
        max_price=sel.xpath(MAXPRICE_XPATH).get()
        details=sel.xpath(DETAILS_XPATH).getall()

        table_data = sel.xpath(TABLEDATA_XPATH)
        data = {}
        for row in table_data:
            key = row.xpath(KEY_XPATH).get(default="").strip()

            # Value can be inside <div> or inside <a>
            value_parts = row.xpath(VALUE_XPATH).getall()
            value = " ".join([v.strip() for v in value_parts if v.strip()])

            data[key] = value
        delivery_in= data.get("Delivery In")
        compound=data.get("Compound")
        sale_type=data.get("Sale Type")
        finishing=data.get("Finishing")

        # CLEAN
        location = location.strip() if location else ""
        #price=price.replace("EGP","").strip() if price else ""
        #max_price=max_price.replace("EGP","").strip() if max_price else ""
        #details = "".join(det.strip() for det in details) if details else ""
        delivery_in=delivery_in.strip() if delivery_in else ""
        compound= compound.strip() if compound else ""
        sale_type = sale_type.strip() if sale_type else ""
        finishing=finishing.strip() if finishing else ""
        price=meta.get('product',{}).get("price")
        maxprice=meta.get('product',{}).get("max_price")
        maxprice= str(maxprice) if price != maxprice else ""
        
        # ITEM YEILD
        item = {}
        item["url"] = meta.get('product', {}).get('url')
        item['title'] = meta.get('product', {}).get('title')
        item["location"] = location
        item["price"] = str(price)
        item["max_price"] = maxprice
        item["type"] = "property"
        item['property_type'] = meta.get('product', {}).get('property_type')
        item["details"] = meta.get('product',{}).get("details")
        item["reference_number"] = str(meta.get('product', {}).get('refernce_number'))
        item['bedrooms'] = str(meta.get('product', {}).get('bedrooms'))
        item['bathrooms'] = str(meta.get('product', {}).get('bathrooms'))
        item["delivery_in"] = str(delivery_in)
        item["compound"] = compound
        item["sale_type"] = sale_type
        item["finishing"] = finishing
        item["ready_by"] = meta.get('product',{}).get("ready_by")
        item["iteration_number"]="2025_12"
        item["date"] = scraped_ts
        

        # product_item = ProductDataItem(**item)
        # self.mongo.process(product_item, collection=MONGO_COLLECTION_DATA)

        logging.info(item)
        try:
            self.mongo[MONGO_COLLECTION_DATA].insert_one(item)
        except:
            pass


if __name__ == "__main__":
    parser_obj = Parser()
    parser_obj.start()
    parser_obj.close()