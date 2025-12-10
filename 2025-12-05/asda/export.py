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

        def dict_to_string(d):
            if not d:
                return ""
            return ", ".join(f"{k}: {v}" for k, v in d.items())

        cursor = self.mongo[MONGO_COLLECTION_DATA].find(no_cursor_timeout=True)
        unique_ids = set()
        unique_urls = set()

        filtered_items = []
        for item in cursor:
           
            uid = item.get("product_id")
            url = item.get("url")
            upc = item.get("upc")

            if not uid or uid in unique_ids:
                continue

            if not url or url in unique_urls:
                continue

            if upc in [None, "", "None"]:
                continue
            unique_ids.add(uid)
            unique_urls.add(url)

            filtered_items.append(item)

            if len(filtered_items) >= 200:
                break
        for item in filtered_items:
            def remove_css(text):
                if not text:
                    return ""
                else:
                    # Remove all `.something{...}` patterns (CSS rules)
                    text = re.sub(r'\.[\w\-]+\s*[^}]*\{[^}]*\}\s*', '', text)

                    # Optionally remove multiple CSS blocks in a row
                    text = re.sub(r'(\.[\w\-]+\s*[^}]*\{[^}]*\}\s*)+', '', text)

                    return text.strip()
            try:
                # === BASIC FIELDS ===
                unique_id=item.get("product_id","")#not null
                competitor_name="asda"#not null
                store_name="asda"
                extraction_date=datetime.now().strftime("%Y-%m-%d")#not null
                product_name=item.get("name").replace("|","")#notnull
                brand=item.get("brand")
                #-----------------------------------------------------
                size = item.get("package_size")
                if size:
                    size_value = str(size).strip().upper()

                    # Normalize separators like 'x', 'X', '*'
                    size_clean = re.sub(r'[\*X]', 'x', size_value)

                    grammage_quantity = ""
                    grammage_unit = ""

                    # ------------------------------
                    # CASE 1: PATTERN LIKE "2x10ML", "2*10ML", "2 X 10 ML"
                    # ------------------------------
                    multi_pattern = r"^\s*([0-9]+)\s*x\s*([0-9]+)\s*([A-Z]+)\s*$"
                    multi_match = re.match(multi_pattern, size_clean)
                    if multi_match:
                        grammage_quantity = f"{multi_match.group(1)}x{multi_match.group(2)}"
                        grammage_unit = multi_match.group(3)
                    
                    else:
                        # ------------------------------
                        # CASE 2: SIMPLE NUMBER + UNIT (e.g., "250G", "10 ML")
                        # ------------------------------
                        simple_pattern = r"^\s*([0-9]+)\s*([A-Z]+)\s*$"
                        simple_match = re.match(simple_pattern, size_clean)

                        if simple_match:
                            grammage_quantity = simple_match.group(1)
                            grammage_unit = simple_match.group(2)

                        else:
                            # ------------------------------
                            # CASE 3: WORDS ONLY (EACH, BOX, PER GB, PCS)
                            # ------------------------------
                            word_pattern = r"^\s*([A-Z ]+)\s*$"
                            word_match = re.match(word_pattern, size_clean)

                            if word_match:
                                grammage_quantity = size_clean
                                grammage_unit = ""
                            else:
                                # fallback
                                grammage_quantity = size_clean
                                grammage_unit = ""
                else:
                    grammage_quantity = ""
                    grammage_unit = ""
                #-----------------------------------------------level 1 not null
                breadcrumb=item.get("breadcrumbs")
                # Split breadcrumb by '>' and clean each part
                hierarchy_parts = [b.strip() for b in breadcrumb.split(">") if b.strip()]

                # Create up to 7 hierarchy levels (fill missing ones with "")
                hierarchy_levels = {}
                for i in range(7):
                    hierarchy_levels[f"producthierarchy_level{i+1}"] = hierarchy_parts[i] if i < len(hierarchy_parts) else ""
                #------------------------------------------------------
                price=item.get("price")
                was_price=item.get("wasprice")
                #print(price,was_price)
                if not was_price:
                    regular_price=f"{float(price):.2f}"
                    selling_price=f"{float(price):.2f}"
                    promotion_price=""
                    price_was=""
                else:
                    regular_price=f"{float(was_price):.2f}"
                    price_was=f"{float(was_price):.2f}"
                    selling_price=f"{float(price):.2f}"
                    promotion_price=f"{float(price):.2f}"
                #--------------------------------------------------------
                offer=item.get("offer")
                promo=item.get("promos")
                if offer == "List": 
                    promotion_description=promo
                else:
                    promotion_description=promo or offer
                #-------------------------------------------------------------
                price_per_unit=item.get("priceperuom")
                currency=item.get("currency")
                pdp_url=item.get("url")
                product_description=remove_css(dict_to_string(item.get("description",{})))
                storage_instructions=remove_css((item.get("description",{})).get("Storage"))
                preparation_instructions=remove_css((item.get("description",{})).get("Cooking Guidelines"))
                instructionforuse=remove_css((item.get("description",{})).get("Preparation and Usage"))
                country_of_origin=remove_css((item.get("description",{})).get("Country of Origin"))
                allergens =item.get("allergy")
                nutritional_information=remove_css(item.get("nutritional_values"))
                #-----------------------------------------------------------------
                frozens=item.get("frozen")
                if frozens == "Frozen":
                    frozen=frozens 
                else: 
                    frozen=""
                #--------------------------------------------------------------
                rating=item.get("avg_rating")
                review=item.get("rating_count")
                image_url_1=item.get("images")
                competitor_product_key=unique_id
                upc=item.get("upc")
                features=remove_css((item.get("description",{})).get("Features"))
                dietary_lifestyle=item.get("lifestyle")
                manufacturer_address=remove_css((item.get("description",{})).get("Manufacturer Address"))
                recycling_information=remove_css((item.get("description",{})).get("Recycling Info"))
                site_shown_uom=size
                ingredients=remove_css((item.get("description",{})).get("Ingredients"))
                instock= True if item.get("stock") == "A" or item.get("stock") == "I" else False
                product_unique_key=f"{unique_id}P"
                Warning=remove_css((item.get("description",{})).get("Safety Warning"))
                

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
                    "brand": brand or "",
                    "brand_type": "",
                    "grammage_quantity": grammage_quantity or "",
                    "grammage_unit": grammage_unit.lower() or "",
                    "drained_weight": "",
                    **hierarchy_levels,
                    "regular_price": regular_price,
                    "selling_price": selling_price,
                    "price_was":price_was,
                    "promotion_price": promotion_price,
                    "promotion_valid_from": "",
                    "promotion_valid_upto": "",
                    "promotion_type": "",
                    "percentage_discount": "",
                    "promotion_description": promotion_description or "",
                    "package_sizeof_sellingprice": "",
                    "per_unit_sizedescription": "",
                    "price_valid_from": "",
                    "price_per_unit": price_per_unit or "",
                    "multi_buy_item_count": "",
                    "multi_buy_items_price_total": "",
                    "currency": currency,
                    "breadcrumb": breadcrumb,
                    "pdp_url": pdp_url,
                    "variants": "",
                    "product_description": product_description or "",
                    "instructions":"" ,
                    "storage_instructions": storage_instructions or "",
                    "preparationinstructions": preparation_instructions or "",
                    "instructionforuse": instructionforuse or "",
                    "country_of_origin": country_of_origin or "",
                    "allergens": allergens or "",
                    "age_of_the_product": "",
                    "age_recommendations": "",
                    "flavour": "",
                    "nutritions": "",
                    "nutritional_information": nutritional_information or "",
                    "vitamins": "",
                    "labelling": frozens or "",
                    "grade": "",
                    "region": "",
                    "packaging": "",
                    "receipies": "",
                    "processed_food": "",
                    "barcode": "",
                    "frozen": frozen or "",
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
                    "rating": rating or "",
                    "review": review or "",
                    "file_name_1":"",
                    "image_url_1":image_url_1 or "",
                    "file_name_2":"",
                    "image_url_2":"",
                    "file_name_3":"",
                    "image_url_3":"",
                    "competitor_product_key": competitor_product_key or "",
                    "fit_guide": "",
                    "occasion": "",
                    "material_composition": "",
                    "style": "",
                    "care_instructions": "",
                    "heel_type": "",
                    "heel_height": "",
                    "upc": upc or "",
                    "features": features or "",
                    "dietary_lifestyle": dietary_lifestyle or "",
                    "manufacturer_address": manufacturer_address or "",
                    "importer_address": "",
                    "distributor_address": "",
                    "vinification_details": "",
                    "recycling_information": recycling_information or "",
                    "return_address": "",
                    "alchol_by_volume": "",
                    "beer_deg": "",
                    "netcontent": "",
                    "netweight": "",
                    "site_shown_uom": site_shown_uom or "",
                    "ingredients": ingredients or "",
                    "random_weight_flag": "",
                    "instock": instock or "",
                    "promo_limit": "",
                    "product_unique_key": product_unique_key,
                    "multibuy_items_pricesingle": "",
                    "perfect_match": "",
                    "servings_per_pack": "",
                    "warning": Warning.replace("WARNING","").strip() or "",
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
