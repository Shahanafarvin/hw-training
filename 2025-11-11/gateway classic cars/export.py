import csv
import logging
import re
from pymongo import MongoClient
from settings import MONGO_DB, MONGO_COLLECTION_DATA, FILE_NAME, FILE_HEADERS


class Export:
    """Post-Processing for eReplacementParts Project"""

    def __init__(self, writer):
        """Initialize Mongo and CSV writer"""
        self.client = MongoClient("mongodb://localhost:27017/")
        self.mongo = self.client[MONGO_DB]
        self.writer = writer

    def clean_html(self, text):
        """Remove HTML tags safely"""
        if not text:
            return ""
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)
        
        # Replace multiple newlines/tabs/spaces with a single space
        text = re.sub(r"[\r\n\t]+", " ", text)
        
        # Replace line breaks or multiple spaces before labels (e.g., Diameter:) with commas
        text = re.sub(r"\s{2,}", " ", text).strip()
        text = re.sub(r"\s*,\s*", ", ", text)
        
        # Add comma for new line like segments (simulate paragraph joins)
        text = re.sub(r"\s{2,}", ", ", text)
        
        return text.strip(" ,")

    def start(self):
        """Export data from MongoDB to CSV"""
        self.writer.writerow(FILE_HEADERS)
        logging.info(f"CSV headers written: {FILE_HEADERS}")

        for item in self.mongo[MONGO_COLLECTION_DATA].find(no_cursor_timeout=True):
            make=item.get("make","").strip()
            model=item.get("model","").strip()
            year=item.get("year","")
            vin=item.get("VIN","")
            price=item.get("price","")
            mileage=item.get("mileage","")
            transmission=item.get("transmission","").strip()
            engine=item.get("engine","").strip()
            color=item.get("color","").strip()
            fuel_type=item.get("fuel_type","").strip()
            body_style=item.get("body_style","").strip()
            description=self.clean_html(item.get("description","").strip())
            image_URLs=item.get("image_url","").strip()
            source_link=item.get("source_link","").strip()
            fuel_type=""

            data = [
                make,
                model,
                year,
                vin,
                price,
                mileage,
                transmission,
                engine,
                color,
                fuel_type,
                body_style,
                description,
                image_URLs,
                source_link,
                fuel_type
            ]

            self.writer.writerow(data)

        logging.info(" Data export completed successfully!")

    def close(self):
        """Close Mongo connection"""
        self.client.close()


if __name__ == "__main__":

    with open(FILE_NAME, "w", encoding="utf-8", newline="") as file:
        writer_file = csv.writer(file, delimiter=",", quotechar='"')
        export = Export(writer_file)
        export.start()
        export.close()
