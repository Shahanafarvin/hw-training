import csv
import json
from datetime import datetime
from pymongo import MongoClient
from settings import MONGO_DB, MONGO_COLLECTION_DATA, FILE_HEADERS, FILE_NAME, logging



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
                # === EXTRACT RAW DATA ===
                url= item.get("url", "")
                unique_id= item.get("sku", "")
                product_name = item.get("product_name", "")
                breadcrumbs= item.get("breadcrumbs", "")
                rating= item.get("rating", "")
                reviews= item.get("reviews", "")
                currency= item.get("currency", "")  
                selling_price= item.get("selling_price", "")
                regular_price= item.get("regular_price", "")
                price_label= item.get("price_label", "")    
                priceValidUntil= item.get("priceValidUntil", "")    
                availability= item.get("availability", "")    
                seller= item.get("seller", "")
                features= item.get("features", "")
                description= item.get("description", "")
                specification= item.get("specification", {})
                mpn= item.get("mpn", "")

                hierarchy_parts = [b.strip() for b in breadcrumbs.split(">") if b.strip()]

                # Create up to 7 hierarchy levels (fill missing ones with "")
                hierarchy_levels = {}
                for i in range(7):
                    hierarchy_levels[f"producthierarchy_level{i+1}"] = hierarchy_parts[i] if i < len(hierarchy_parts) else ""

                # === IMAGES (limit 7) ===
                images = item.get("image") or []
                if not isinstance(images, list):
                    images = [images] if images else []
                image_data = {}
                for i in range(1, 8):
                    image = images[i - 1] if len(images) >= i else ""
                    image_data[f"image_url_{i}"] = image

                try:
                    selling_price = float(selling_price) if selling_price else 0
                except:
                    selling_price = 0

                try:
                    regular_price = float(regular_price) if regular_price else 0
                except:
                    regular_price = 0

                discount = round(((regular_price - selling_price) / regular_price * 100), 2) \
                        if regular_price > selling_price > 0 else ""

                # === BUILD CLEAN RECORD ===
                cleaned_data = {
                    "unique_id":unique_id ,
                    "competitor_name": "halfords" ,
                    "store_name": "halfords",
                    "store_addressline1": "",
                    "store_addressline2": "",
                    "store_suburb": "",
                    "store_state": "",
                    "store_postcode": "",
                    "store_addressid": "",
                    "extraction_date": datetime.now().strftime("%Y-%m-%d"),
                    "product_name": product_name,
                    "brand": seller ,
                    "brand_type": "",
                    "grammage_quantity": "",
                    "grammage_unit": "",
                    "drained_weight": "",
                    **hierarchy_levels,
                    "regular_price": regular_price if regular_price != 0 else selling_price,
                    "selling_price": selling_price,
                    "price_was": regular_price if regular_price > selling_price else "",
                    "promotion_price":selling_price if selling_price < regular_price else "",
                    "promotion_valid_from": "",
                    "promotion_valid_upto": priceValidUntil,
                    "promotion_type": "",
                    "percentage_discount": discount,
                    "promotion_description": price_label,
                    "package_sizeof_sellingprice": "",
                    "per_unit_sizedescription": "",
                    "price_valid_from": "",
                    "price_per_unit": "",
                    "multi_buy_item_count": "",
                    "multi_buy_items_price_total": "",
                    "currency": currency,
                    "breadcrumb": breadcrumbs,
                    "pdp_url": url,
                    "variants": "",
                    "product_description": description,
                    "instructions": "",
                    "storage_instructions": "",
                    "preparationinstructions": "",
                    "instructionforuse": "",
                    "country_of_origin":"" ,
                    "allergens":"" ,
                    "age_of_the_product": "",
                    "age_recommendations": "",
                    "flavour": "",
                    "nutritions": "",
                    "nutritional_information": "",
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
                    "special_information": json.dumps(specification, ensure_ascii=False),
                    "label_information": "",
                    "dimensions": specification.get("Dimensions", ""),
                    "special_nutrition_purpose": "",
                    "feeding_recommendation": "",
                    "warranty": "",
                    "color": specification.get("primary colour", ""),
                    "model_number": "",
                    "material": specification.get("Material", ""),
                    "usp": "",
                    "dosage_recommendation": "",
                    "tasting_note": "",
                    "food_preservation": "",
                    "size": "",
                    "rating": rating,
                    "review": reviews,
                    **image_data,
                    "competitor_product_key": mpn,
                    "fit_guide": "",
                    "occasion": "",
                    "material_composition": "",
                    "style": "",
                    "care_instructions": "",
                    "heel_type": "",
                    "heel_height": "",
                    "upc": "",
                    "features": features,
                    "dietary_lifestyle": "",
                    "manufacturer_address": "",
                    "importer_address": "",
                    "distributor_address": "",
                    "vinification_details": "",
                    "recycling_information": "",
                    "return_address": "",
                    "alchol_by_volume": "",
                    "beer_deg": "",
                    "netcontent": "",
                    "netweight": specification.get("Weight", ""),
                    "site_shown_uom": "",
                    "ingredients": "",
                    "random_weight_flag": "",
                    "instock": str(availability).lower() == "instock",
                    "promo_limit": "",
                    "product_unique_key": f"{unique_id}P",
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
