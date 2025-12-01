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
        DESCRIPTION_XPATH = "//div[@data-cy='description-container']//text()"
        AMENITIES_XPATH = "//div[@itemprop='amenityFeature']//text()"
        PHOTOS_XPATH = "//div[@class='imageContainer']/div"
        DETAILS_XPATH = "//div[@class='sc-32ba891c-0 bfaAYI']//text()"
        PHONE_XPATH = "//a[@itemprop='url']/@href"

        # EXTRACT
        location = sel.xpath(LOCATION_XPATH).get()
        description_list = sel.xpath(DESCRIPTION_XPATH).getall()
        amenities_list = sel.xpath(AMENITIES_XPATH).getall()
        photos_list = sel.xpath(PHOTOS_XPATH).getall()
        details_list = sel.xpath(DETAILS_XPATH).getall()
        scraped_ts = datetime.now().strftime("%Y-%m-%d")
        phone_number = sel.xpath(PHONE_XPATH).get()

        # CLEAN
        location = location.strip() if location else ""
        description = " ".join(description_list).strip() if description_list else ""
        amenities = ",".join(amenities_list).strip() if amenities_list else ""
        number_of_photos = len(photos_list) if photos_list else 0
        details = ",".join(details_list).strip() if details_list else ""
        phone_number = phone_number.replace("tel:", "").strip() if phone_number else ""

        # ITEM YEILD
        item = {}
        item["id"] = meta.get('product', {}).get('id')
        item["reference_number"] = meta.get('product', {}).get('refernce_number')
        item["url"] = meta.get('product', {}).get('url')
        item["broker_display_name"] = meta.get('product', {}).get('broker_display_name')
        item["broker"] = meta.get('product', {}).get('broker')
        item['title'] = meta.get('product', {}).get('title')
        item["description"] = description
        item["location"] = location
        item["price"] = meta.get('product', {}).get('price')
        item["currency"] = meta.get('product', {}).get('currency')
        item['bedrooms'] = meta.get('product', {}).get('bedrooms')
        item['bathrooms'] = meta.get('product', {}).get('bathrooms')
        item['scraped_ts'] = scraped_ts
        item["amenities"] = amenities
        item["details"] = details
        item["number_of_photos"] = number_of_photos
        item["phone_number"] = phone_number
        item["date"] = scraped_ts
        item['property_type'] = meta.get('product', {}).get('property_type')

        # product_item = ProductDataItem(**item)
        # self.mongo.process(product_item, collection=MONGO_COLLECTION_DATA)

        #logging.info(item)
        try:
            self.mongo[MONGO_COLLECTION_DATA].insert_one(item)
        except:
            pass


if __name__ == "__main__":
    parser_obj = Parser()
    parser_obj.start()
    parser_obj.close()