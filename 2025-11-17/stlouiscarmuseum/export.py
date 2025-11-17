import csv
import re
from items import ProductItem
from mongoengine import connect
from settings import MONGO_DB, FILE_NAME, FILE_HEADERS, logging


class Export:
    """Post-Processing: Export MongoDB data to CSV"""

    def __init__(self, writer):
        connect(db=MONGO_DB, host="localhost", alias="default", port=27017)
        self.writer = writer
    
    def clean_html(self, text):
        """Remove HTML tags safely and normalize whitespace"""
        if not text:
            return ""
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"[\r\n\t]+", " ", text)
        text = re.sub(r"\s{2,}", " ", text)
        text = re.sub(r"\s*,\s*", ", ", text)
        return text.strip(" ,")
    
    def start(self):
        """Export as CSV file"""
        self.writer.writerow(FILE_HEADERS)
        logging.info(f"CSV Headers: {FILE_HEADERS}")

        for item in ProductItem.objects():  
            
            try:
                year_val = int(item.year or 0)
                if year_val > 1990:
                    continue
            except ValueError:
                continue

            source_link = item.source_link or ""
            make = item.make or ""
            model = item.model or ""
            year = item.year or ""
            VIN = item.VIN or ""
            price = item.price.replace("$","").replace("now","").replace(",","").strip() or ""
            mileage = item.mileage.replace("\nMiles","").strip() or ""
            transmission = item.transmission or ""
            engine = item.engine or ""
            color = item.color or ""
            fuel_type = item.fuel_type or ""
            body_style = item.body_style or ""
            description = self.clean_html(item.description)
            image_URL = item.image_URL or ""

            # Prepare data row
            data = [
                 make, model, year, VIN, price, mileage,
                transmission, engine, color, fuel_type, body_style,
                description, image_URL,source_link,
            ]

            self.writer.writerow(data)


if __name__ == "__main__":
    with open(FILE_NAME, "w", newline="", encoding="utf-8") as file:
        writer_file = csv.writer(file, delimiter=",", quotechar='"')
        export = Export(writer_file)
        export.start()
        logging.info(f"Data exported to {FILE_NAME}")
