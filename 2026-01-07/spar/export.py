import csv
import json
import re
from html import unescape

INPUT_JSON = "/home/shahana/datahut-training/hw-training/2026-01-07/spar/spar_products_details.json"
OUTPUT_CSV = "/home/shahana/datahut-training/hw-training/2026-01-07/spar/spar_2026_01_07_sample.csv"

csv_headers =[
  "pdp_url",
  "article_number",
  "brand",
  "product_name",
  "size",
  "regular_price",
  "selling_price",
  "price_per_unit",
  "promotion_description",
  "product_description",
  "additional_information",
  "ingredients",
  "allergens",
  "nutrition_info",
  "preparation_instructions",
  "preparation_methods",
  "identification_marking",
  "country_of_origin",
  "storage_instructions",
  "instructions_for_use",
  "variant",
  "country"
]

class SparExport:
    def __init__(self, writer):
        self.writer = writer
    
    def start(self):
        # write header
        self.writer.writerow(csv_headers)

        with open(INPUT_JSON, encoding="utf-8") as infile:
            products = json.load(infile)  # <-- JSON ARRAY
            def clean_value(val):
                if val is None:
                    return ""
                val = str(val)
                val = unescape(val)           # remove HTML entities
                val = re.sub(r"<.*?>", "", val)  # remove HTML tags
                val = re.sub(r"\s+", " ", val)   # replace multiple spaces/newlines with single space
                return val.strip()
            
            for product in products:
                priceperunit=product.get("price_per_unit", "")
                # split into key-value pairs
                parts = dict(
                    item.strip().split(": ", 1)
                    for item in priceperunit.split(",")
                )

                price = parts.get("price")
                quantity = parts.get("quantity")
                unit = parts.get("unit")

                price_per_unit = f"Per {quantity} {unit} {price}"
                row = {
                    "pdp_url": product.get("pdp_url", ""),
                    "article_number": product.get("article_number", ""),
                    "brand": product.get("brand", ""),
                    "product_name": product.get("product_name", ""),
                    "size": product.get("size", ""),
                    "regular_price": str(product.get("regular_price", "")),
                    "selling_price": str(product.get("selling_price", "")),
                    "price_per_unit": price_per_unit,
                    "promotion_description": clean_value(product.get("promotion_description", "")),
                    "product_description": clean_value(product.get("product_description", "")),
                    "additional_information":clean_value(product.get("additional_information", "")),
                    "ingredients": clean_value(product.get("ingredients", "")),
                    "allergens": clean_value(product.get("allergens", "")),
                    "nutrition_info": clean_value(product.get("nutrition_info", "")),
                    "preparation_instructions": clean_value(product.get("preparation_instructions", "")),
                    "preparation_methods": clean_value(product.get("preparation_methods", "")),
                    "identification_marking": clean_value(product.get("identification_marking", "")),
                    "country_of_origin": clean_value(product.get("country_of_origin", "")),
                    "storage_instructions": clean_value(product.get("storage_instructions", "")),
                    "instructions_for_use": clean_value(product.get("instructions_for_use", "")),
                    "variant": product.get("variant", ""),
                    "country": product.get("country", "")
                }

                self.writer.writerow([row.get(h, "") for h in csv_headers])

if __name__ == "__main__":
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quotechar='"', quoting=csv.QUOTE_MINIMAL)
        exporter = SparExport(writer)
        exporter.start()
