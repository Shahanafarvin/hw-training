import csv
from pymongo import MongoClient
from datetime import datetime
from settings import (
    MONGO_DB,
    MONGO_COLLECTION_DATA,
    FILE_HEADERS,
    FILE_NAME,
    logging
)


class Export:
    """Export MongoDB collection to CSV with cleaning and normalization"""

    def __init__(self, writer):
        client = MongoClient("mongodb://localhost:27017/")
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
                unique_id = str(item.get("sku"))
                competitor_name = "auchan"
                product_name = clean_text(item.get("title"))
                brand = clean_text(item.get("brand"))
                grammage_quantity = clean_text(item.get("grammage_quantity"))
                grammage_unit = clean_text(item.get("grammage_unit"))
                regular_price = format_price(item.get("regular_price"))
                selling_price = format_price(item.get("discounted_price"))
                if regular_price != selling_price: 
                    price_was=regular_price
                    promotion_price=regular_price
                else:
                    price_was=""
                    promotion_price="" 
                percentage_discount = format_price(item.get("discount"))
                currency = clean_text(item.get("currency"))
                pdp_url = clean_text(item.get("product_url"))
                breadcrumb = clean_text(item.get("breadcrumbs"))
                allergens = clean_text(item.get("allergens"))
                description = clean_text(item.get("description"))
                ingredients = clean_text(item.get("ingredients"))
                

                # === PARAMETERS CLEANING ===
                parameters = item.get("parameters", [])
                country_of_origin = ""
                manufacturer_address = ""
                all_parameters = []
                for param in parameters:
                    name = param.get("name", "").lower()
                    value = clean_text(param.get("value", ""))
                    if "származási ország" in name:
                        country_of_origin = value
                    elif "forgalmazó" in name:
                        manufacturer_address = value

                    # Store all parameters as "Name: Value"
                    all_parameters.append(f"{name}: {value}")
                # Convert list of parameters into single comma-separated string
                all_parameters_str = ", ".join(all_parameters)

                # === NUTRITION CLEANING ===
                nutrition_data = item.get("nutrition", [])
                nutritions = "; ".join(
                    [f"{n[0]}: {n[2]}" for n in nutrition_data if len(n) > 2 and n[0] and n[2]]
                )

                # === IMAGES (limit 3) ===
                images = item.get("images", [])
                image_data = {}
                for i in range(1, 8):
                    url = images[i - 1] if len(images) >= i else ""
                    image_data[f"image_url_{i}"] = url

               
                # Split breadcrumb by '>' and clean each part
                hierarchy_parts = [b.strip() for b in breadcrumb.split(">") if b.strip()]

                # Create up to 7 hierarchy levels (fill missing ones with "")
                hierarchy_levels = {}
                for i in range(7):
                    hierarchy_levels[f"producthierarchy_level{i+1}"] = hierarchy_parts[i] if i < len(hierarchy_parts) else ""

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
                    "extraction_date": datetime.now().strftime("%Y-%m-%d"),
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
                    "percentage_discount": percentage_discount,
                    "promotion_description": "",
                    "package_sizeof_sellingprice": "",
                    "per_unit_sizedescription": "",
                    "price_valid_from": "",
                    "price_per_unit": "",
                    "multi_buy_item_count": "",
                    "multi_buy_items_price_total": "",
                    "currency": currency,
                    "breadcrumb": breadcrumb,
                    "pdp_url": pdp_url,
                    "variants": "",
                    "product_description": description,
                    "instructions": "",
                    "storage_instructions": "",
                    "preparationinstructions": "",
                    "instructionforuse": "",
                    "country_of_origin": country_of_origin,
                    "allergens": allergens,
                    "age_of_the_product": "",
                    "age_recommendations": "",
                    "flavour": "",
                    "nutritions": nutritions,
                    "nutritional_information": nutritions,
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
                    "special_information": "",
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
                    "rating": "",
                    "review": "",
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
                    "features": all_parameters_str,
                    "dietary_lifestyle": "",
                    "manufacturer_address": manufacturer_address,
                    "importer_address": "",
                    "distributor_address": "",
                    "vinification_details": "",
                    "recycling_information": "",
                    "return_address": "",
                    "alchol_by_volume": "",
                    "beer_deg": "",
                    "netcontent": "",
                    "netweight": "",
                    "site_shown_uom": "",
                    "ingredients": ingredients,
                    "random_weight_flag": "",
                    "instock": "1",
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
