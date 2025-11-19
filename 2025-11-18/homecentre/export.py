import csv
import re
import logging
from time import sleep
from mongoengine import connect
from settings import MONGO_DB, FILE_NAME, FILE_HEADERS
from items import ProductItem

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")

class Export:
    """Export ProductItem collection to CSV"""

    def __init__(self, writer):
        self.writer = writer
        connect(db=MONGO_DB, host="localhost", alias="default")  # connect to MongoDB

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
        logging.info(f"Headers written: {FILE_HEADERS}")

        for item in ProductItem.objects():
            url=item.url
            product_id=item.product_id
            product_name=item.product_name
            product_color=item.product_color
            material=item.material
            quantity=item.quantity
            details_string=self.clean_html(item.details_string)
            specification=item.specification
            price=item.price
            wasprice=item.wasprice
            product_type=item.product_type
            breadcrumb=item.breadcrumb
            stock=item.stock
            image=",".join(item.image) if item.image else ""
            data = [
                url,
                product_id,
                product_name,
                product_color,
                material,
                quantity,
                details_string,
                specification,
                price,
                wasprice,
                product_type,
                breadcrumb,
                stock,
                image,
            ]

            self.writer.writerow(data)
            logging.info(f"Exported: {item.product_name}")
            

if __name__ == "__main__":
    with open(FILE_NAME, "w", encoding="utf-8", newline="") as file:
        writer_file = csv.writer(file, delimiter=",", quotechar='"')
        export = Export(writer_file)
        export.start()
