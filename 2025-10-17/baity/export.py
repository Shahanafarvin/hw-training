import csv
import logging
from pymongo import MongoClient
from settings import (
    MONGO_DB,
    MONGO_COLLECTION_URL,
    FILE_NAME,
)

# Define your CSV headers (you can adjust as needed)
FILE_HEADERS = [
    "url",
    "title",
    "price",
    "agency_name",
    "agency_contact_number",
    "governorate",
    "area",
    "property_type",
    "property_size",
    "rate_per_sqft",
    "rooms",
    "bathrooms",
    "roads",
    "parking",
    "built_up_area",
    "classification",
]

class Export:
    """Exports crawled property data from MongoDB to CSV"""

    def __init__(self, writer):
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client[MONGO_DB]
        self.collection = self.db[MONGO_COLLECTION_URL]
        self.writer = writer

    def start(self):
        """Export data to CSV"""
        self.writer.writerow(FILE_HEADERS)
        logging.info(f"Exporting fields: {FILE_HEADERS}")

        count = 0
        for item in self.collection.find({}, no_cursor_timeout=True):
            try:
                row = [
                    item.get("url", ""),
                    item.get("title", ""),
                    item.get("price", ""),
                    item.get("agency_name", ""),
                    item.get("agency_contact_number", ""),
                    item.get("governorate", ""),
                    item.get("area", ""),
                    item.get("property_type", ""),
                    item.get("property_size", ""),
                    item.get("rate_per_sqft", ""),
                    item.get("rooms", ""),
                    item.get("bathrooms", ""),
                    item.get("roads", ""),
                    item.get("parking", ""),
                    item.get("built_up_area", ""),
                    item.get("classification", ""),
                ]
                self.writer.writerow(row)
                count += 1

                if count % 500 == 0:
                    logging.info(f" Exported {count} records so far...")

            except Exception as e:
                logging.error(f"Error exporting record: {e}")
                continue

        logging.info(f" Export complete — total records: {count}")
        self.client.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    output_file = f"{FILE_NAME}.csv"

    with open(output_file, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, delimiter=",", quotechar='"')
        exporter = Export(writer)
        exporter.start()

    logging.info(f" File saved as: {output_file}")
