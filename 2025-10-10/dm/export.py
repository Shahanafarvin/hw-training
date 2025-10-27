import csv
from pymongo import MongoClient
from datetime import datetime
from settings import MONGO_DB, MONGO_COLLECTION_DATA, FILE_HEADERS, file_name, logging


class Export:
    """Post-Processing Export with Cleaning"""

    def __init__(self, writer):
        """Initialize MongoDB and CSV writer"""
        client = MongoClient("mongodb://localhost:27017/")
        self.mongo = client[MONGO_DB] 
        self.writer = writer

    def start(self):
        """Export as CSV file"""
        self.writer.writerow(FILE_HEADERS)
        logging.info("File headers written successfully.")

        cursor = self.mongo[MONGO_COLLECTION_DATA].find(no_cursor_timeout=True)

        for item in cursor:
            try:
                # === CLEANING HELPERS ===
                def clean_text(value):
                    """Clean up text fields"""
                    return str(value).replace("\n", " ").replace("\r", " ").replace("{", " ").replace("}", " ").strip() if value else ""

                def format_price(value):
                    """Ensure price always has 2 decimals"""
                    try:
                        return f"{float(value):.2f}"
                    except (TypeError, ValueError):
                        return ""

                unique_id = clean_text(item.get("unique_id"))
                brand = clean_text(item.get("brand"))
                product_name = clean_text(item.get("product_name"))
                breadcrumb = clean_text(item.get("breadcrumb"))

                # Hierarchy levels (1–7)
                hierarchy = [clean_text(item.get(f"producthierarchy_level_{i}", "")) for i in range(1, 8)]

                # Image URLs and file names (up to 6)
                image_data = {}
                for i in range(1, 7):
                    url = clean_text(item.get(f"image_url_{i}", ""))
                    image_data[f"image_url_{i}"] = url
                   

                # Clean other text fields
                description = clean_text(item.get("product_description"))
                instructionforuse = clean_text(item.get("instructionforuse"))
                instructions = clean_text(item.get("instructions"))
                ingredients = clean_text(item.get("ingredients"))
                manufacturer_address = clean_text(item.get("manufacturer_address"))
                storage_instructions = clean_text(item.get("storage_instructions"))
                preparationinstructions = clean_text(item.get("preparationinstructions"))
                country_of_origin = clean_text(item.get("country_of_origin"))
                allergens = clean_text(item.get("allergens"))
                features = clean_text(item.get("features"))
                organictype = clean_text(item.get("organictype"))
                variants = clean_text(item.get("variants"))

                # Numeric values
                regular_price = format_price(item.get("regular_price"))
                selling_price = format_price(item.get("selling_price"))
               

                # === BASE DATA CONSTRUCTION ===
                cleaned_data = {
                    "unique_id": unique_id,
                    "competitor_name": clean_text(item.get("competitor_name")).replace(".at", " "),
                    "extraction_date": item.get("extraction_date", datetime.now()).strftime("%Y-%m-%d"),
                    "product_name": product_name,
                    "brand": brand,
                    "grammage_quantity": clean_text(item.get("grammage_quantity")),
                    "grammage_unit": clean_text(item.get("grammage_unit")),
                    "regular_price": regular_price,
                    "selling_price": selling_price,
                    "currency": clean_text(item.get("currency")),
                    **{f"producthierarchy_level{i+1}": hierarchy[i] for i in range(7)},
                    "breadcrumb": breadcrumb,
                    "pdp_url": clean_text(item.get("pdp_url")),
                    "variants": variants,
                    **image_data,
                    "product_description": description,
                    "instructionforuse": instructionforuse,
                    "instructions": instructions,
                    "ingredients": ingredients,
                    "manufacturer_address": manufacturer_address,
                    "storage_instructions": storage_instructions,
                    "preparationinstructions": preparationinstructions,
                    "country_of_origin": country_of_origin,
                    "allergens": allergens,
                    "features": features,
                    "organictype": "Organic" if organictype else "Non-Organic",
                    "product_unique_key": clean_text(item.get("product_unique_key")),
                }

                # === FILL MISSING HEADERS SAFELY ===
                row = [cleaned_data.get(field, "") for field in FILE_HEADERS]

                self.writer.writerow(row)

            except Exception as e:
                logging.error(f"Error processing item {item.get('unique_id', 'UNKNOWN')}: {e}")

        cursor.close()
        logging.info("Export completed successfully.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    with open(file_name, "w", encoding="utf-8", newline="") as file:
        writer_file = csv.writer(file, delimiter="|", quotechar='"')
        export = Export(writer_file)
        export.start()
