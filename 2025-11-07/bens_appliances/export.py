import csv
import logging
import re
from pymongo import MongoClient
from settings import MONGO_DB, MONGO_COLLECTION_DATA, file_name, FILE_HEADERS


class Export:
    """Post-Processing for Ben's Appliances"""

    def __init__(self, writer):
        client = MongoClient("mongodb://localhost:27017/")
        self.mongo = client[MONGO_DB] 
        self.writer = writer

    def clean_description_and_equivalents(self, text, existing_equivalents):
        """Cleans description (handles HTML if present) and extracts equivalent part numbers."""

        # Convert to string safely
        text = str(text)

        #  Remove HTML tags *only if present*
        if "<" in text and ">" in text:
            text = re.sub(r"<[^>]*>", " ", text)

        # Replace HTML entities and unwanted chars
        text = (
            text.replace("&nbsp;", " ")
            .replace("&amp;", "&")
            .replace("\xa0", " ")
        )

        #  Normalize spaces, tabs, and newlines
        text = re.sub(r"\s+", " ", text).strip()

        #  Extract equivalent part numbers if missing
        if not existing_equivalents:
            pattern = r"\b[A-Z0-9]+[A-Z0-9]*\s*\([^)]+\)"
            matches = re.findall(pattern, text)
            if matches:
                existing_equivalents = ", ".join(sorted(set(matches)))

        return text, existing_equivalents
    
    def start(self):
        """Export as CSV file"""

        # Write headers once
        self.writer.writerow(FILE_HEADERS)
        logging.info(f"CSV headers written: {FILE_HEADERS}")

        # Iterate over all products in the MongoDB collection
        for item in self.mongo[MONGO_COLLECTION_DATA].find(no_cursor_timeout=True):
            # Extract fields safely using .get()
            url = item.get("url", "")
            title = item.get("title", "")
            manufacturer = item.get("manufacturer", "")
            price = item.get("price", "").replace("Sale price","").strip()
            description = item.get("description", "")
            oem_part_number = ""
            retailer_part_number = ""
            competitor_part_numbers = ""
            compatible_products = ""
            equivalent_part_numbers = item.get("equivalent_part_numbers", "")
            product_specifications = ""
            additional_description = ""
            availability = item.get("availability", "")
            image_urls = item.get("image_urls", "")
            linked_files = ""

            
            if isinstance(image_urls, list):
                image_urls = ", ".join(image_urls)
            # Clean description and extract equivalents if missing
            description, equivalent_part_numbers = self.clean_description_and_equivalents(
                description, equivalent_part_numbers
            )
            
            # Prepare CSV row
            data = [
                url,
                title,
                manufacturer,
                price,
                description,
                oem_part_number,
                retailer_part_number,
                competitor_part_numbers,
                compatible_products,
                equivalent_part_numbers,
                product_specifications,
                additional_description,
                availability,
                image_urls,
                linked_files,
            ]

            # Write to CSV
            self.writer.writerow(data)


if __name__ == "__main__":
    with open(file_name, "a", encoding="utf-8", newline="") as file:
        writer_file = csv.writer(file, delimiter=",", quotechar='"')
        export = Export(writer_file)
        export.start()
