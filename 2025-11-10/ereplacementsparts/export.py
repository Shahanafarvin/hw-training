import csv
import logging
import re
from pymongo import MongoClient
from settings import MONGO_DB, MONGO_COLLECTION_PRODUCT_DETAILS, FILE_NAME, FILE_HEADERS


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

        for item in self.mongo[MONGO_COLLECTION_PRODUCT_DETAILS].find(no_cursor_timeout=True):
            url = item.get("url", "").strip()
            product_name = item.get("product_name", "").strip()
            price = item.get("price", "").strip()
            currency = "USD"
            oem_part_for = item.get("oem_part_for", "").strip()
            part_number = item.get("part_number", "").strip()
            availability = item.get("availability", "").strip()
            breadcrumbs = " > ".join(item.get("breadcrumbs", [])) if isinstance(item.get("breadcrumbs"), list) else item.get("breadcrumbs", "")
            description = self.clean_html(item.get("description", ""))
            additional_description = self.clean_html(item.get("additional_description", ""))

            data = [
                url,
                product_name,
                price,
                currency,
                oem_part_for,
                part_number,
                availability,
                breadcrumbs,
                description,
                additional_description,
            ]

            self.writer.writerow(data)

        logging.info(" Data export completed successfully!")

    def close(self):
        """Close Mongo connection"""
        self.client.close()


if __name__ == "__main__":
    

    FILE_NAME = "ereplacementparts_export.csv"

    with open(FILE_NAME, "w", encoding="utf-8", newline="") as file:
        writer_file = csv.writer(file, delimiter=",", quotechar='"')
        export = Export(writer_file)
        export.start()
        export.close()
