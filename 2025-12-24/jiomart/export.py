
import re
import csv
from re import sub
from html import unescape
from pymongo import MongoClient
from settings import (
    MONGO_DB,
    MONGO_COLLECTION_DATA,
    FILE_NAME
)

csv_headers = [
    "unique_id",
    "retailer_name",
    "extraction_date",
    "product_name",
    "brand",
    "brand_type",
    "grammage_quantity",
    "grammage_unit",
    "producthierarchy_level1",
    "producthierarchy_level2",
    "producthierarchy_level3",
    "producthierarchy_level4",
    "producthierarchy_level5",
    "regular_price",
    "selling_price",
    "promotion_price",
    "promotion_valid_from",
    "promotion_valid_upto",
    "promotion_type",
    "percentage_discount",
    "promotion_description",
    "price_per_unit",
    "currency",
    "breadcrumb",
    "product_type",
    "item_form",
    "package_type",
    "pdp_url",
    "flavour",
    "product_description",
    "instructions",
    "storage_instructions",
    "country_of_origin",
    "allergens",
    "organictype",
    "file_name_1",
    "file_name_2",
    "file_name_3",
    "file_name_4",
    "file_name_5",
    "file_name_6",
    "upc",
    "ingredients",
    "servings_per_pack"
]


class Export:
    """PostProcessing - MongoDB to CSV Export"""

    def __init__(self, writer):
        self.writer = writer
        self.mongo = MongoClient().get_database(MONGO_DB)

    def clean_text(self, text):
        if not text:
            return ""
        return sub(r"<.*?>|\s+", " ", unescape(str(text))).strip()

    def start(self):
        self.writer.writerow(csv_headers)

        for item in self.mongo[MONGO_COLLECTION_DATA].find():

            # ---------- BASIC ----------
            unique_id = item.get("unique_id", "")
            retailer_name = "jiomart"
            product_name = item.get("product_name", "")
            brand = item.get("brand", "")
            product_type = item.get("product_type", "")
            item_form = item.get("item_form", "")
            pdp_url = item.get("url", "")

            # ---------- PRICE ----------
            regular_price = item.get("regular_price", "")
            selling_price = item.get("selling_price", "")

            try:
                regular_price = f"{float(regular_price):.2f}"
                selling_price = f"{float(selling_price):.2f}"
            except:
                regular_price = ""
                selling_price = ""

            promotion_price = selling_price if regular_price and regular_price != selling_price else ""
            percentage_discount = item.get("discount_percentage", "")
            promotion_description = (
                f"{percentage_discount} % Off" if percentage_discount else ""
            )

            # ---------- BREADCRUMB ----------
            breadcrumb = item.get("breadcrumbs", "")
            levels = [b.strip() for b in breadcrumb.split(">")]

            producthierarchy = {}
            for i in range(5):
                producthierarchy[f"producthierarchy_level{i+1}"] = (
                    levels[i] if i < len(levels) else ""
                )

            # ---------- SIZE / GRAMMAGE ----------
            size_text = (
                item.get("specifications", {}).get("Net Weight")
                or item.get("specifications", {}).get("Net Quantity", "")
            )

            match = re.search(r"([\d.]+)\s*(kg|g|gm|gram|grams)", size_text.lower())
            grammage_quantity = match.group(1) if match else ""
            grammage_unit = match.group(2) if match else ""

            variants = [v.strip() for v in item.get("variants/flavour").split(",")]

            current_size = size_text.strip().lower() if size_text else ""

            filtered = [
                v for v in variants
                if v.lower() != current_size
            ]

            variants=", ".join(filtered)

            # ---------- DESCRIPTION ----------
            product_description = self.clean_text(item.get("description", ""))

            # ---------- IMAGES ----------
            images = item.get("images", "")
            images_list = images.split(",") if images else []

            file_names = {}
            for i in range(1, 7):
                file_names[f"file_name_{i}"] = (
                    f"{unique_id}_{i}.png" if i <= len(images_list) else ""
                )

            # ---------- ORGANIC ----------
            food_type = item.get("food_type", [])
            organictype = "Organic" if "Green Dot" in food_type else "Non-Organic"

            # ---------- ROW ----------
            row = {
                "unique_id": unique_id,
                "retailer_name": retailer_name,
                "extraction_date": item.get("extraction_date"),
                "product_name": product_name,
                "brand": brand,
                "brand_type": "",
                "grammage_quantity": grammage_quantity,
                "grammage_unit": grammage_unit,
                **producthierarchy,
                "regular_price": regular_price,
                "selling_price": selling_price,
                "promotion_price": promotion_price,
                "promotion_valid_from": "",
                "promotion_valid_upto": "",
                "promotion_type": "",
                "percentage_discount": percentage_discount,
                "promotion_description": promotion_description,
                "price_per_unit": "",
                "currency": "INR",
                "breadcrumb": breadcrumb,
                "product_type": product_type,
                "item_form": item_form,
                "package_type": "",
                "pdp_url": pdp_url,
                "variants/flavour": variants,
                "product_description": product_description,
                "instructions": "",
                "storage_instructions": "",
                "country_of_origin": item.get("country_of_origin", ""),
                "allergens": item.get("allergens", ""),
                "organictype": organictype,
                **file_names,
                "upc": "",
                "ingredients": item.get("ingredients", ""),
                "servings_per_pack": ""
            }

            self.writer.writerow([row.get(h, "") for h in csv_headers])


if __name__ == "__main__":
    with open(FILE_NAME, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quotechar='"')
        export = Export(writer)
        export.start()
