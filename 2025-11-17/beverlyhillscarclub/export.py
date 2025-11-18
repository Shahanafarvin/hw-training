import csv
import re
from mongoengine import connect
from items import ProductDataItem
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

        for item in ProductDataItem.objects():

            # ------------------ Assign fields using item.field or "" ------------------
            source_link = item.source_link or ""
            make = item.make or ""
            model = item.model or ""
            year = item.year or ""
            VIN = item.VIN or ""

            price = item.price or ""
            if price:
                price = price.replace("$", "").replace(",", "").strip()

            mileage = ""
            transmission = ""
            engine = ""
            color = item.color or ""
            fuel_type = ""
            body_style = ""

            description = self.clean_html(item.description)
            
            # image_URLs is a LIST → convert to comma string
            image_URLs = item.image_URLs or []
            if isinstance(image_URLs, list):
                image_URLs = ", ".join(image_URLs)

            # ------------------ Prepare row ------------------
            data = [
                make,
                model,
                year,
                VIN,
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
            ]

            self.writer.writerow(data)


# ---------------------- MAIN ----------------------
if __name__ == "__main__":
    with open(FILE_NAME, "w", newline="", encoding="utf-8") as file:
        writer_file = csv.writer(file, delimiter=",", quotechar='"')
        export = Export(writer_file)
        export.start()
        logging.info(f"Data exported to {FILE_NAME}")
