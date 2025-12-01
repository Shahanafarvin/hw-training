import csv
import re
import logging
from pymongo import MongoClient
from settings import MONGO_DB, FILE_NAME, FILE_HEADER, MONGO_COLLECTION_DATA


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")

class Export:
    """Export ProductItem collection to CSV"""

    def __init__(self, writer):
        self.writer = writer
        self.client = MongoClient("localhost", 27017)
        self.db = self.client[MONGO_DB]

    def start(self):
        """Export as CSV file"""
        self.writer.writerow(FILE_HEADER)
        logging.info(f"Headers written: {FILE_HEADER}")

        for item in self.db[MONGO_COLLECTION_DATA].find(no_cursor_timeout=True):
            id = item.get("id", "")
            reference_number = item.get("reference_number", "")
            url = item.get("url", "")
            broker_display_name = item.get("broker_display_name", "")
            broker = item.get("broker", "")
            category = ""
            category_url = ""
            title = item.get("title", "")
            description = item.get("description", "")
            location = item.get("location", "")
            price = item.get("price", "")
            currency = item.get("currency", "")
            price_per = ""
            bedrooms = item.get("bedrooms", "")
            bathrooms = item.get("bathrooms", "")
            furnished = ""
            rera_permit_number = ""
            dtcm_licence = ""
            scraped_ts = item.get("scraped_ts", "")
            amenities = item.get("amenities", "")
            details = item.get("details", "")
            agent_name = ""
            number_of_photos = item.get("number_of_photos", "")
            user_id = ""
            phone_number = item.get("phone_number", "")
            date = item.get("date", "")
            iteration_number = ""
            depth = ""
            property_type = item.get("property_type", "")
            sub_category_1 = ""
            sub_category_2 = ""
            published_at = ""       
            
            data = [
                    id,
                    reference_number,
                    url,
                    broker_display_name,
                    broker,
                    category,
                    category_url,
                    title,
                    description,
                    location,
                    price,
                    currency,
                    price_per,
                    bedrooms,
                    bathrooms,
                    furnished,
                    rera_permit_number,
                    dtcm_licence,
                    scraped_ts,
                    amenities,
                    details,
                    agent_name,
                    number_of_photos,
                    user_id,
                    phone_number,
                    date,
                    iteration_number,
                    depth,
                    property_type,
                    sub_category_1,
                    sub_category_2,
                    published_at,
                ]


            self.writer.writerow(data)
            logging.info(f"Exported: {item.get('title')}")
            

if __name__ == "__main__":
    with open(FILE_NAME, "w", encoding="utf-8", newline="") as file:
        writer_file = csv.writer(file, delimiter=",", quotechar='"')
        export = Export(writer_file)
        export.start()
