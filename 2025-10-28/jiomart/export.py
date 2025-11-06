import csv
import re
from pymongo import MongoClient
from datetime import datetime
from settings import MONGO_URI, MONGO_DB, MONGO_COLLECTION_DATA, FILE_HEADERS, FILE_NAME, logging



class Export:
    """Export MongoDB collection to CSV with cleaning and normalization"""

    def __init__(self, writer):
        client = MongoClient(MONGO_URI)
        self.mongo = client[MONGO_DB]
        self.writer = writer

    def start(self):
        """Export data to CSV"""
        self.writer.writerow(FILE_HEADERS)
        logging.info("File headers written successfully.")

        cursor = self.mongo[MONGO_COLLECTION_DATA].find(no_cursor_timeout=True)

        for item in cursor:
            try:
                # === CLEANING HELPERS ===
                def clean_text(value):
                    """Normalize string fields"""
                    if isinstance(value, list):
                        return "; ".join([str(v).strip() for v in value if v])
                    if isinstance(value, dict):
                        return "; ".join([f"{k}: {v}" for k, v in value.items()])
                    return str(value).replace("\n", " ").replace("\r", " ").strip() if value else ""

                def format_price(value):
                    """Format numeric values"""
                    try:
                        return f"{float(value):.2f}"
                    except (TypeError, ValueError):
                        return ""

                # === BASIC FIELDS ===
                unique_id = str(item.get("product_id", ""))
                competitor_name = "Jiomart"
                extraction_date = datetime.now().strftime("%Y-%m-%d")
                product_name = clean_text(item.get("title", ""))
                brand = clean_text(item.get("brand", ""))

                breadcrumbs=item.get("category_path")[0]
                 # Split breadcrumb by '>' and clean each part
                hierarchy_parts = [b.strip() for b in breadcrumbs.split(">") if b.strip()]

                # Create up to 7 hierarchy levels (fill missing ones with "")
                hierarchy_levels = {}
                for i in range(7):
                    hierarchy_levels[f"producthierarchy_level{i+1}"] = hierarchy_parts[i] if i < len(hierarchy_parts) else ""

                regular_price = format_price(item.get("mrp", ""))
                selling_price = format_price(item.get("selling_price", ""))
                percentage_discount= item.get("discount","")
                
                price_was = regular_price
                promotion_price = selling_price
            
                    
                currency = "INR"
                pdp_url = item.get("pdp_url", "")

                product_description= clean_text(item.get("description", ""))

                instock = True if item.get("availability", "").lower() == "a" else False

                ratings= item.get("average_rating","")
                reviews= item.get("review_count","")
               
                # === IMAGES (limit 7) ===
                images = item.get("images", [])
                image_data = {}
                for i in range(1, 8):
                    url = images[i - 1] if len(images) >= i else ""
                    image_data[f"image_url_{i}"] = url
               
                # === ADDITIONAL FIELDS ===
                features = item.get("product_info", {})
                featur_string = ", ".join(f"{k}: {v}" for k, v in features.items())
                manufacturer_address = features.get("Manufacturer Address", "")
                distributor_address = features.get("Sold By", "")
                country_of_origin = features.get("Country of Origin", "")
                special_information = features.get("Product Type", "")
                instructionforuse = features.get("How To Use", "")
                storage_instructions = features.get("Storage Instructions", "") + features.get("Storage Temperature Limit (in Degree Celsius)", "")
                ingredients = features.get("Ingredients", "")
                nutritional_information= features.get("Nutrient Content", "")
                allergens = features.get("Allergens Included", "")

                value = features.get("Net Quantity", "").strip()  # e.g. "150 g", "1 Pieces", "3 N"
                match = re.match(r"^([\d\.]+)\s*([A-Za-z]+)?", value)
                if match:
                    grammage_quantity = match.group(1)
                    grammage_unit = match.group(2) or ""
                else:
                    grammage_quantity = ""
                    grammage_unit = ""
                site_shown_uom= features.get("Net Quantity", "")
                dietory_lifestyle= features.get("Dietary Preference", "")


                # === BUILD CLEAN RECORD ===
                cleaned_data = {
                    "unique_id": unique_id,
                    "competitor_name": competitor_name,
                    "store_name": "",
                    "store_addressline1": "",
                    "store_addressline2": "",
                    "store_suburb": "",
                    "store_state": "",
                    "store_postcode": "",
                    "store_addressid": "",
                    "extraction_date": extraction_date,
                    "product_name": product_name,
                    "brand": brand,
                    "brand_type": "",
                    "grammage_quantity": grammage_quantity,
                    "grammage_unit": grammage_unit,
                    "drained_weight": "",
                    **hierarchy_levels,
                    "regular_price": regular_price,
                    "selling_price": selling_price,
                    "price_was":price_was,
                    "promotion_price": promotion_price,
                    "promotion_valid_from": "",
                    "promotion_valid_upto": "",
                    "promotion_type": "",
                    "percentage_discount": percentage_discount ,
                    "promotion_description": f"{percentage_discount}% OFF" if float(percentage_discount) > 0 else "",
                    "package_sizeof_sellingprice": "",
                    "per_unit_sizedescription": "",
                    "price_valid_from": "",
                    "price_per_unit": "",
                    "multi_buy_item_count": "",
                    "multi_buy_items_price_total": "",
                    "currency": currency,
                    "breadcrumb": breadcrumbs,
                    "pdp_url": pdp_url,
                    "variants": "",
                    "product_description": product_description,
                    "instructions": "",
                    "storage_instructions": storage_instructions,
                    "preparationinstructions": "",
                    "instructionforuse": instructionforuse,
                    "country_of_origin": country_of_origin,
                    "allergens": allergens,
                    "age_of_the_product": "",
                    "age_recommendations": "",
                    "flavour": "",
                    "nutritions": nutritional_information,
                    "nutritional_information": nutritional_information,
                    "vitamins": "",
                    "labelling": "",
                    "grade": "",
                    "region": "",
                    "packaging": "",
                    "receipies": "",
                    "processed_food": "",
                    "barcode": "",
                    "frozen": "",
                    "chilled": "",
                    "organictype": "",
                    "cooking_part": "",
                    "Handmade": "",
                    "max_heating_temperature": "",
                    "special_information": special_information,
                    "label_information": "",
                    "dimensions": "",
                    "special_nutrition_purpose": "",
                    "feeding_recommendation": "",
                    "warranty": "",
                    "color": "",
                    "model_number": "",
                    "material": "",
                    "usp": "",
                    "dosage_recommendation": "",
                    "tasting_note": "",
                    "food_preservation": "",
                    "size": "",
                    "rating": ratings,
                    "review": reviews,
                    **image_data,
                    "competitor_product_key": "",
                    "fit_guide": "",
                    "occasion": "",
                    "material_composition": "",
                    "style": "",
                    "care_instructions": "",
                    "heel_type": "",
                    "heel_height": "",
                    "upc": "",
                    "features": featur_string,
                    "dietary_lifestyle": dietory_lifestyle,
                    "manufacturer_address": manufacturer_address,
                    "importer_address": "",
                    "distributor_address": distributor_address,
                    "vinification_details": "",
                    "recycling_information": "",
                    "return_address": "",
                    "alchol_by_volume": "",
                    "beer_deg": "",
                    "netcontent": "",
                    "netweight": "",
                    "site_shown_uom": site_shown_uom,
                    "ingredients": re.sub(r"<.*?>", "", ingredients).strip(),
                    "random_weight_flag": "",
                    "instock": instock,
                    "promo_limit": "",
                    "product_unique_key": str(unique_id) + "P",
                    "multibuy_items_pricesingle": "",
                    "perfect_match": "",
                    "servings_per_pack": "",
                    "Warning": "",
                    "suitable_for": "",
                    "standard_drinks": "",
                    "grape_variety": "",
                    "retail_limit": "",
                }

                # === WRITE SAFE ROW ===
                row = [cleaned_data.get(field, "") for field in FILE_HEADERS]
                self.writer.writerow(row)

            except Exception as e:
                logging.error(f"Error processing record {item.get('_id')}: {e}")

        cursor.close()
        logging.info("Export completed successfully.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    with open(FILE_NAME, "w", encoding="utf-8", newline="") as file:
        writer_file = csv.writer(file, delimiter="|", quotechar='"')
        export = Export(writer_file)
        export.start()
