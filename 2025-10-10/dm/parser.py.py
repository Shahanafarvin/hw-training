import logging
import re
import time
import requests
from datetime import datetime
from mongoengine import connect, errors
from items import ProductUrlItem, ProductDetailItem
from settings import HEADERS, MONGO_DB

class Parser:
    """Parsing product details from DM Austria API using MongoEngine"""

    def __init__(self):
        connect(db=MONGO_DB, alias="default", host="localhost", port=27017)
        self.api_base = "https://products.dm.de/product/products/detail/AT/gtin/"

    def start(self):
        """Start parsing process"""
        products = ProductUrlItem.objects()  # Fetch all products from MongoDB
        logging.info(f"Found {products.count()} products to process")

        for idx, prod in enumerate(products, start=1):
            gtin = prod.gtin
            url = prod.url
            if not gtin:
                continue

            result = self.fetch_product_detail(gtin, url)
            if result:
                try:
                    product_item = ProductDetailItem(**result)
                    product_item.save(force_insert=True)
                    logging.info(f"Saved {gtin} ({idx}/{products.count()})")
                except errors.NotUniqueError:
                    logging.info(f"Skipped duplicate GTIN {gtin}")

            time.sleep(0.6)  # polite delay

        logging.info("All products processed successfully.")

    def fetch_product_detail(self, gtin, url):
        """Fetch product data from DM API"""
        api_url = f"{self.api_base}{gtin}"
        try:
            r = requests.get(api_url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                data = r.json()
                return self.parse_item(data, gtin, url)
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
                        text = " ".join([t for t in texts_data if isinstance(t, str)])
                    else:
                        text = ""

                    bulletpoints = " ".join(block.get("bulletpoints") or [])
                    desc_list = block.get("descriptionList") or []

                    if "produktbeschreibung" in header:
                        product_description.append(f"{text} {bulletpoints}")
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
                        usage_instructions += text.strip() + " "
                    elif "warnhinweise" in header:
                        warnings += text.strip() + " "
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

            match = re.search(r"([\d.,]+)\s*([a-zA-Z]+)", title.get("headline"))
            if match:
                grammage_quantity = match.group(1).replace(",", ".")
                grammage_unit = match.group(2)

            variants = [
                opt.get("label", "")
                for color in data.get("variants", {}).get("colors", [])
                for opt in color.get("options", [])
                if isinstance(opt, dict)
            ]

            # Dynamic breadcrumb levels
            product_hierarchy = {f"producthierarchy_level_{i+1}": b for i, b in enumerate(breadcrumbs[:7])}
            for i in range(len(breadcrumbs), 7):
                product_hierarchy[f"producthierarchy_level_{i+1}"] = ""

            # Dynamic extraction of image URLs and standardized file names
            image_data = {}
            for i, img in enumerate(images[:6]):
                src = img.get("src", "")
                image_data[f"image_url_{i+1}"] = src
                image_data[f"file_name_{i+1}"] = f"{data.get('gtin')}_{i+1}.png" if data.get('gtin') else ""

            # Fill remaining slots (if fewer than 6 images)
            for i in range(len(images), 6):
                image_data[f"image_url_{i+1}"] = ""
                image_data[f"file_name_{i+1}"] = ""

            product_data = {
                "unique_id": data.get("gtin"),
                "competitor_name": "dm.at",
                "extraction_date": datetime.now(),
                "product_name": title.get("headline"),
                "brand": brand.get("name"),
                "grammage_quantity": grammage_quantity,
                "grammage_unit": grammage_unit,
                "regular_price": f"{float(metadata.get('price')):.2f}",
                "selling_price": f"{float(metadata.get('price')):.2f}",    
                "price_was": f"{float(metadata.get('price')):.2f}",
                "promotion_price": f"{float(metadata.get('price')):.2f}",
                "currency": seo_info.get("priceCurrency", "EUR"),
                **product_hierarchy,
                "breadcrumb": " > ".join([b for b in breadcrumbs if b]),
                "pdp_url": url,
                "variants":"colors :" + str(variants) if variants else "",
                **image_data,
                "product_description": " ".join(product_description).strip(),
                "instructionforuse": usage_instructions.strip(),
                "instructions": warnings.strip(),
                "ingredients": ingredients,
                "manufacturer_address": manufacturer_address,
                "storage_instructions": storage_instructions,
                "preparationinstructions": preparation,
                "country_of_origin": made_in,
                "allergens": allergens,
                "features": str(product_features),
                "organictype": organic,
                "instock": True if metadata.get("price") else False,
                "upc": data.get("dan"),
                "product_unique_key": str(data.get("gtin")) + "P"
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


if __name__ == "__main__":
    parser_obj = Parser()
    parser_obj.start()
