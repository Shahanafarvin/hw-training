import csv
import logging
import re
import json
from mongoengine import connect
from settings import MONGO_DB, FILE_NAME, FILE_HEADERS
from items import ProductDetailItem

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class Export:
    """Post-Processing for Matalan products to CSV"""

    def __init__(self, writer):
        """Initialize Mongo and CSV writer"""
        connect(db=MONGO_DB, alias="default", host="localhost", port=27017)
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
        """Export data from MongoDB to CSV"""
        self.writer.writerow(FILE_HEADERS)
        logging.info(f"CSV headers written: {FILE_HEADERS}")

        for item in ProductDetailItem.objects():
            # Base fields
            url = item.product_url or ""
            name = item.name or ""
            size = item.size or ""
            color = item.color or ""
            quantity = "" 
            brand = item.brand_name or ""
            product_info = self.clean_html(item.product_information)
            currency = item.currency or ""
            price = item.price or ""
            product_id = item.product_id or ""
            price_before_discount = item.price_before_discount or ""
            gender = ""
            material = ""
            specifications = item.specifications or {}
            if specifications:
                gender = specifications.get("Gender", "")
                material = self.clean_html(specifications.get("Material", ""))

            labeling = item.labeling or ""
            availability = item.stock_status or ""
            category_name = item.category_name or ""
            product_type = ""  
            breadcrumbs = item.breadcrumbs or ""
            picture = item.image_url or ""

            data = [
                url,
                name,
                size,
                color,
                quantity,
                brand,
                product_info,
                currency,
                price,
                product_id,
                price_before_discount,
                gender,
                picture,
                json.dumps(specifications, ensure_ascii=False),  # specifications as JSON string
                breadcrumbs,
                material,
                labeling,
                availability,
                category_name,
                product_type,
            ]

            self.writer.writerow(data)

        logging.info("✓ Data export completed successfully!")

    def close(self):
        """Close writer if needed"""
        logging.info("Export finished.")


if __name__ == "__main__":
    with open(FILE_NAME, "w", encoding="utf-8", newline="") as file:
        writer_file = csv.writer(file, delimiter=",", quotechar='"')
        exporter = Export(writer_file)
        exporter.start()
        exporter.close()
