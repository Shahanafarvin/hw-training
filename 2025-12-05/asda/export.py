import csv
import re
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
                unique_id = item.get("unique_id")
                competitor_name = item.get("competitor_name")
                extraction_date = item.get("extraction_date")
                product_name = item.get("product_name")
                brand = item.get("brand")
                grammage_quantity = item.get("grammage_quantity")
                grammage_unit = item.get("grammage_unit")
                producthierarchy_level1 = item.get("producthierarchy_level1")
                producthierarchy_level2 = item.get("producthierarchy_level2")
                producthierarchy_level3 = item.get("producthierarchy_level3")
                producthierarchy_level4 = item.get("producthierarchy_level4")
                producthierarchy_level5 = item.get("producthierarchy_level5")
                producthierarchy_level6 = item.get("producthierarchy_level6")
                producthierarchy_level7 = item.get("producthierarchy_level7")
                regular_price = item.get("regular_price")
                selling_price = item.get("selling_price")
                promotion_price = item.get("promotion_price")
                price_was = item.get("price_was")
                promotion_description = item.get("promotion_description")
                price_per_unit = item.get("price_per_unit")
                currency = item.get("currency")
                breadcrumb = item.get("breadcrumb")
                pdp_url = item.get("pdp_url")
                product_description = item.get("product_description")
                storage_instructions = item.get("storage_instructions")
                preparation_instructions = item.get("preparation_instructions")
                instructionforuse = item.get("instructionforuse")
                country_of_origin = item.get("country_of_origin")
                allergens = item.get("allergens")
                nutritional_information = item.get("nutritional_information")
                labelling = item.get("labelling")
                frozen = item.get("frozen")
                rating = item.get("rating")
                review = item.get("review")
                image_url_1 = item.get("image_url_1")
                competitor_product_key = item.get("competitor_product_key")
                upc = item.get("upc")
                Features = item.get("Features")
                dietary_lifestyle = item.get("dietary_lifestyle")
                manufacturer_address = item.get("manufacturer_address")
                recycling_information = item.get("recycling_information")
                site_shown_uom = item.get("site_shown_uom")
                ingredients = item.get("ingredients")
                instock = item.get("instock")
                product_unique_key = item.get("product_unique_key")
                warning = item.get("warning")
                netcontent = item.get("netcontent")

                #
                cleaned_data = {
                    "unique_id":unique_id,
                    "competitor_name":competitor_name,
                    "store_name": "",
                    "store_addressline1": "",
                    "store_addressline2": "",
                    "store_suburb": "",
                    "store_state": "",
                    "store_postcode": "",
                    "store_addressid": "",
                    "extraction_date":extraction_date,
                    "product_name": product_name,
                    "brand": brand,
                    "brand_type": "",
                    "grammage_quantity":grammage_quantity,
                    "grammage_unit":grammage_unit,
                    "drained_weight": "",
                    "producthierarchy_level1":producthierarchy_level1,
                    "producthierarchy_level2":producthierarchy_level2,
                    "producthierarchy_level3":producthierarchy_level3,
                    "producthierarchy_level4":producthierarchy_level4,
                    "producthierarchy_level5":producthierarchy_level5,
                    "producthierarchy_level6":producthierarchy_level6,
                    "producthierarchy_level7":producthierarchy_level7,
                    "regular_price": regular_price,
                    "selling_price": selling_price,
                    "price_was":price_was,
                    "promotion_price": promotion_price,
                    "promotion_valid_from": "",
                    "promotion_valid_upto": "",
                    "promotion_type": "",
                    "percentage_discount": "",
                    "promotion_description": promotion_description,
                    "package_sizeof_sellingprice": "",
                    "per_unit_sizedescription": "",
                    "price_valid_from": "",
                    "price_per_unit": price_per_unit,
                    "multi_buy_item_count": "",
                    "multi_buy_items_price_total": "",
                    "currency": currency,
                    "breadcrumb": breadcrumb,
                    "pdp_url": pdp_url,
                    "variants": "",
                    "product_description": product_description ,
                    "instructions":"" ,
                    "storage_instructions": storage_instructions ,
                    "preparationinstructions": preparation_instructions,
                    "instructionforuse": instructionforuse ,
                    "country_of_origin": country_of_origin,
                    "allergens": allergens,
                    "age_of_the_product": "",
                    "age_recommendations": "",
                    "flavour": "",
                    "nutritions": "",
                    "nutritional_information": nutritional_information or "",
                    "vitamins": "",
                    "labelling": labelling,
                    "grade": "",
                    "region": "",
                    "packaging": "",
                    "receipies": "",
                    "processed_food": "",
                    "barcode": "",
                    "frozen": frozen,
                    "chilled": "",
                    "organictype": "",
                    "cooking_part": "",
                    "handmade": "",
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
                    "rating": rating ,
                    "review": review ,
                    "file_name_1":"",
                    "image_url_1":image_url_1,
                    "file_name_2":"",
                    "image_url_2":"",
                    "file_name_3":"",
                    "image_url_3":"",
                    "competitor_product_key": competitor_product_key ,
                    "fit_guide": "",
                    "occasion": "",
                    "material_composition": "",
                    "style": "",
                    "care_instructions": "",
                    "heel_type": "",
                    "heel_height": "",
                    "upc": upc or "",
                    "features": Features,
                    "dietary_lifestyle": dietary_lifestyle,
                    "manufacturer_address": manufacturer_address,
                    "importer_address": "",
                    "distributor_address": "",
                    "vinification_details": "",
                    "recycling_information": recycling_information,
                    "return_address": "",
                    "alchol_by_volume": "",
                    "beer_deg": "",
                    "netcontent": netcontent,
                    "netweight": "",
                    "site_shown_uom": site_shown_uom ,
                    "ingredients": ingredients,
                    "random_weight_flag": "",
                    "instock": instock,
                    "promo_limit": "",
                    "product_unique_key": product_unique_key,
                    "multibuy_items_pricesingle": "",
                    "perfect_match": "",
                    "servings_per_pack": "",
                    "warning": warning,
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
