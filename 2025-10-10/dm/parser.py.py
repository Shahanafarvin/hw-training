import logging
import re
import time
import requests
from datetime import datetime
from pymongo import MongoClient
from settings import HEADERS, MONGO_COLLECTION_CATEGORY, MONGO_COLLECTION_DATA, MONGO_DB


class Parser:
    """Parsing product details from DM Austria API"""

    def __init__(self):
        self.mongo = MongoClient("mongodb://localhost:27017/")
        self.db = self.mongo[MONGO_DB]
        self.input_collection = self.db[MONGO_COLLECTION_CATEGORY]
        self.output_collection = self.db[MONGO_COLLECTION_DATA]
        self.api_base = "https://products.dm.de/product/products/detail/AT/gtin/"

    def start(self):
        """Start parsing process"""
        products = list(self.input_collection.find())
        logging.info(f"Found {len(products)} products to process")

        processed = 0
        for prod in products:
            gtin = prod.get("gtin")
            url = prod.get("product_url")
            if not gtin:
                continue

            result = self.fetch_product_detail(gtin, url)
            if result:
                self.output_collection.update_one(
                    {"unique_id": result["unique_id"]},
                    {"$set": result},
                    upsert=True
                )
                processed += 1
                logging.info(f"Saved {gtin} ({processed}/{len(products)})")

            time.sleep(0.6)

        logging.info("All products processed successfully.")

    def fetch_product_detail(self, gtin, url):
        """Fetch product data from DM API"""
        api_url = f"{self.api_base}{gtin}"
        try:
            r = requests.get(api_url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                data = r.json()
                return self.parse_item(data, gtin, url)
            else:
                logging.warning(f"Failed ({r.status_code}) for GTIN {gtin}")
                return None
        except Exception as e:
            logging.error(f"Error fetching GTIN {gtin}: {e}")
            return None

    def parse_item(self, data, gtin, url):
        """Extract structured product details"""
        try:
            seo_info = data.get("seoInformation", {}).get("structuredData", {})
            metadata = data.get("metadata", {})
            title = data.get("title", {})
            brand = data.get("brand", {})
            breadcrumbs = self.extract_breadcrumbs(data.get("breadcrumbs", []))
            images = data.get("images", [])
            desc_groups = data.get("descriptionGroups") or []

            product_description, product_features = [], {}
            ingredients = usage_instructions = warnings = allergens = ""
            preparation = manufacturer_address = storage_instructions = made_in = organic = ""

            for group in desc_groups:
                if not isinstance(group, dict):
                    continue
                header = (group.get("header") or "").lower()
                content_blocks = group.get("contentBlock") or []

                for block in content_blocks:
                    if not isinstance(block, dict):
                        continue
                    texts_data = block.get("texts", [])
                    if isinstance(texts_data, str):
                        text = texts_data.strip()
                    elif isinstance(texts_data, list):
                        text = "\n".join([t for t in texts_data if isinstance(t, str)])
                    else:
                        text = ""

                    bulletpoints = "\n".join(block.get("bulletpoints") or [])
                    desc_list = block.get("descriptionList") or []

                    if "produktbeschreibung" in header:
                        product_description.append(f"{text}\n{bulletpoints}")
                    elif "produktmerkmale" in header:
                        for item in desc_list:
                            if isinstance(item, dict):
                                t = item.get("title", "").strip()
                                d = item.get("description", "").strip()
                                if t and d:
                                    product_features[t] = d
                    elif "inhaltsstoffe" in header or "zutaten" in header:
                        ingredients = text.strip()
                    elif "verwendungshinweise" in header:
                        usage_instructions += text.strip() + "\n"
                    elif "warnhinweise" in header:
                        warnings += text.strip() + "\n"
                    elif "allergene" in header:
                        allergens = text.strip()
                    elif "zubereitung" in header:
                        preparation = text.strip()
                    elif "anschrift" in header:
                        manufacturer_address = text.strip()
                    elif "aufbewahrung" in header:
                        storage_instructions = text.strip()
                    elif "hergestellt in" in header:
                        made_in = text.strip()
                    elif "pflichthinweise" in header:
                        organic = text.strip()

            infos_text = metadata.get("infos") or []
            grammage_quantity, grammage_unit = "", ""
            if infos_text:
                first_info = infos_text[0]
                match = re.match(r"([\d,.]+)\s*([a-zA-Z]+)", first_info)
                if match:
                    grammage_quantity = match.group(1).replace(",", ".")
                    grammage_unit = match.group(2)

            variants = [
                opt.get("label", "")
                for color in data.get("variants", {}).get("colors", [])
                for opt in color.get("options", [])
                if isinstance(opt, dict)
            ]

            product_data = {
                "unique_id": data.get("dan"),
                "competitor_name": "DM Austria",
                "extraction_date": datetime.now().strftime("%Y-%m-%d"),
                "product_name": title.get("headline"),
                "brand": brand.get("name"),
                "grammage_quantity": grammage_quantity,
                "grammage_unit": grammage_unit,
                "regular_price": metadata.get("price") or seo_info.get("price"),
                "currency": seo_info.get("priceCurrency", "EUR"),
                "per_unit_sizedescription": infos_text[0] if infos_text else "",
                "producthierarchy_level_1": breadcrumbs[0],
                "producthierarchy_level_2": breadcrumbs[1],
                "producthierarchy_level_3": breadcrumbs[2],
                "producthierarchy_level_4": breadcrumbs[3],
                "producthierarchy_level_5": breadcrumbs[4],
                "producthierarchy_level_6": breadcrumbs[5],
                "producthierarchy_level_7": breadcrumbs[6],
                "breadcrumb": " > ".join([b for b in breadcrumbs if b]),
                "pdp_url": url,
                "variants": variants,
                "image_url_1": images[0]["src"] if len(images) > 0 else "",
                "image_url_2": images[1]["src"] if len(images) > 1 else "",
                "image_url_3": images[2]["src"] if len(images) > 2 else "",
                "image_url_4": images[3]["src"] if len(images) > 3 else "",
                "image_url_5": images[4]["src"] if len(images) > 4 else "",
                "image_url_6": images[5]["src"] if len(images) > 5 else "",
                "product_description": "\n".join(product_description).strip(),
                "instructionforuse": usage_instructions.strip(),
                "instructions": warnings.strip(),
                "ingredients": ingredients,
                "manufacturer_address": manufacturer_address,
                "storage_instructions": storage_instructions,
                "preparationinstructions": preparation,
                "country_of_origin": made_in,
                "allergens": allergens,
                "features": product_features,
                "organictype": organic,
                "instock": True if metadata.get("price") else False,
            }

            logging.info(f"Parsed GTIN {gtin}")
            return product_data

        except Exception as e:
            logging.error(f"Error parsing GTIN {gtin}: {e}")
            return None

    def extract_breadcrumbs(self, breadcrumbs):
        """Safely extract breadcrumbs"""
        names = []
        if not breadcrumbs:
            return [""] * 7
        for b in breadcrumbs[:7]:
            if isinstance(b, dict) and "name" in b:
                names.append(b["name"])
            elif isinstance(b, str):
                names.append(b)
            else:
                names.append("")
        while len(names) < 7:
            names.append("")
        return names

    def close(self):
        """Close DB connection"""
        self.mongo.close()


if __name__ == "__main__":
    parser_obj = Parser()
    parser_obj.start()
    parser_obj.close()
