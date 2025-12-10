import csv
import re
import logging
from time import sleep
from pymongo import MongoClient
from settings import MONGO_DB, FILE_NAME, FILE_HEADERS, MONGO_COLLECTION_DATA

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")

class Export:
    """Export ProductItem collection to CSV"""

    def __init__(self, writer):
        self.writer = writer
        self.mongo = MongoClient("localhost", 27017)
        self.db = self.mongo[MONGO_DB]

    def start(self):
        self.writer.writerow(FILE_HEADERS)
        logging.info(f"Headers written: {FILE_HEADERS}")

        # Track unique values
        seen_unique_ids = set()
        seen_urls = set()

        exported_count = 0
        max_export = 200

        def extract_gender(breadcrumbs: str) -> str:
            parts = [p.strip().lower() for p in breadcrumbs.split(">")]

            if not parts:
                return ""
            level1 = parts[0]

            if level1 in ["men", "women"]:
                return level1.capitalize()

            if level1 == "kids":
                for p in parts[1:]:
                    if "girl" in p:
                        return "Girls"
                    if "boy" in p:
                        return "Boys"
                    if "unisex" in p:
                        return "Unisex"
                return ""

            return ""

        def dict_to_string(d):
            if not d:
                return ""
            return ", ".join(f"{k}: {v}" for k, v in d.items())

        def clean_html(text):
            if not text:
                return ""
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"[\r\n\t]+", " ", text)
            text = re.sub(r"\s{2,}", " ", text)
            text = re.sub(r"\s*,\s*", ", ", text)
            return text.strip(" ,")

        cursor = self.db[MONGO_COLLECTION_DATA].find(no_cursor_timeout=True)

        for item in cursor:

            # Handle keys with trailing space
            unique_id = item.get("unique_id") or item.get("unique_id ") or ""
            url = item.get("url") or ""

            # Skip duplicates
            if unique_id in seen_unique_ids or url in seen_urls:
                continue

            # Register as seen
            seen_unique_ids.add(unique_id)
            seen_urls.add(url)

            # Stop at 200 rows
            if exported_count >= max_export:
                logging.info("Reached 200 unique rows. Stopping export.")
                break

            product_name = item.get("product_name") or ""
            product_details = clean_html(dict_to_string(item.get("product_details"))) or ""
            color = item.get("color") or ""
            quantity = item.get("quantity") or ""
            size = ", ".join(item.get("size")) if isinstance(item.get("size"), list) else ""
            selling_price = item.get("selling_price")
            regular_price = item.get("regular_price")
            image = item.get("image")
            description = clean_html(item.get("description"))
            currency = item.get("currency")
            breadcrumbs = item.get("breadcrumbs") or ""
            gender = extract_gender(breadcrumbs)
            extraction_date = item.get("extraction_date")

            data = [
                unique_id,
                url,
                product_name,
                product_details,
                color,
                quantity,
                size,
                selling_price,
                regular_price,
                image,
                description,
                currency,
                gender,
                breadcrumbs,
                extraction_date
            ]

            self.writer.writerow(data)
            exported_count += 1
            logging.info(f"Exported ({exported_count}/200): {product_name}")

        cursor.close()


if __name__ == "__main__":
    with open(FILE_NAME, "w", encoding="utf-8", newline="") as file:
        writer_file = csv.writer(file, delimiter=",", quotechar='"')
        export = Export(writer_file)
        export.start()
