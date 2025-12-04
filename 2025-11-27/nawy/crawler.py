import logging
import json
import requests
from pymongo import MongoClient
from settings import HEADERS, API_URL, MONGO_DB, MONGO_COLLECTION_URLS, proxies
#from items import ProductUrlItem


class Crawler:
    """Crawling URLs"""

    def __init__(self):
        self.mongo = MongoClient("localhost", 27017)[MONGO_DB]

    def start(self):
        """Begin crawling pagination"""

        meta = {
            "category": API_URL,
            "start": 1,
            "page_number": 1,
            "total_collected": 0,
            "total_properties": None
        }

        while True:
            payload = {"show": "property", "start": meta["start"]}

            response = requests.post(
                API_URL, headers=HEADERS, proxies=proxies, data=json.dumps(payload)
            )

            if response.status_code != 200:
                logging.error(f"Request failed: {response.status_code}")
                break

            data_response = response.json()
            properties = data_response.get("values", [])
            total_properties = data_response.get("total_properties")

            # Set total_properties only once
            if meta["total_properties"] is None:
                meta["total_properties"] = total_properties

            logging.info(
                f"[Page {meta['page_number']}] start={meta['start']} "
                f"→ received {len(properties)} items"
            )

            # Parse and store items
            is_next = self.parse_item(properties)

            if not is_next:
                logging.info("Pagination completed (no more items).")
                break

            # Update counters
            meta["total_collected"] += len(properties)
            meta["start"] += len(properties)
            meta["page_number"] += 1

            # Stop if we collected all available items
            if meta["total_collected"] >= meta["total_properties"]:
                logging.info(
                    f"Reached total properties {meta['total_properties']}. Stopping."
                )
                break

    def parse_item(self, properties):
        """Extract and save items"""

        if not properties:
            return False

        for prop in properties:
            id = prop.get("id") 
            compound_slug = prop.get("compound", {}).get("slug") 
            property_slug = prop.get("slug") 
            url = f"https://www.nawy.com/compound/{compound_slug}/property/{property_slug}" 
            price=prop.get("min_price")
            max_price = prop.get("max_price") 
            title = prop.get("name") 
            bathrooms = prop.get("number_of_bathrooms") 
            bedrooms = prop.get("number_of_bedrooms") 
            property_type = prop.get("property_type", {}).get("name") 
            min_unit_area=prop.get("min_unit_area")
            max_unit_area=prop.get("max_unit_area")
            details=f"{min_unit_area}m²~{max_unit_area}m²" if max_unit_area != min_unit_area else f"{max_unit_area}m²"
            ready_by=prop.get("min_ready_by")
            
            # ITEM YEILD 
            item = {} 
            item['id'] = id 
            item['refernce_number'] = id 
            item['url'] = url 
            item['price'] = price 
            item['max_price'] = max_price
            item['title'] = title 
            item['bathrooms'] = bathrooms 
            item['bedrooms'] = bedrooms 
            item['property_type'] = property_type
            item['details']=details
            item['ready_by']=ready_by

            #product_item = ProductUrlItem(**item)
            #self.mongo.process(product_item, collection=MONGO_COLLECTION_URLS)

            #logging.info(item)

            try:
                self.mongo[MONGO_COLLECTION_URLS].insert_one(item)
            except:
                pass

        return True

    def close(self):
        """Close DB connection"""
        self.mongo.close()


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
