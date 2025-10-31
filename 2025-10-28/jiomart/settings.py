import logging
import os

# -----------------------
# MongoDB Settings
# -----------------------
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "jiomart_data"
MONGO_COLLECTION_CATEGORY = "jiomart_category_tree"
MONGO_COLLECTION_PRODUCTS = "jiomart_products"
MONGO_COLLECTION_DATA= "jiomart_product_enriched"

# -----------------------
# Logging Configuration
# -----------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

cookies = {
    "nms_mgo_city": "Mumbai",
    "nms_mgo_state_code": "MH",
    "nms_mgo_pincode": "400008",
}

#-----------------------
# category api config
#----------------------
category_api_url = "https://www.jiomart.com/moonx/rest/v1/homepage/trexcategorydetails?type=1&category=2"
categoory_headers = {
    "accept": "*/*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "location_details": '{"city":"Mumbai","state_code":"MH","store_code":{"LOCALSHOPS":{"3P":["3P38SR7XFC60","3PFUIPOCFC01","3PT3LXIHFC05","3P13PK7AFC18","3P38SR7XFC33","3P2G9P4DFC02","3P38SR7XFC67"]},"GROCERIES":{"3P":["groceries_zone_non-essential_services","general_zone","groceries_zone_essential_services"],"1P":["T9V1"]},"FASHION":{"3P":["fashion_zone","general_zone"],"1P":["S535","R975","S402","SURR","R300","SLI1","V017","SB41","TG1K","SLE4","SLTP","T4QF","SANR","S0XN","SANS","SL7Q","SZBL","SANQ","Y524","S4LI","SH09","V027","SJ14","V012"]},"JEWELLERY":{"1P":["VLOR"]},"PREMIUMFRUITS":{"1P":["S575"]},"BOOKS":{"3P":["general_zone"],"1P":["SANR","SANS","SURR","SANQ","S4LI"]},"FURNITURE":{"3P":["general_zone"],"1P":["440","254","60","270"]},"SPORTSTOYSLUGGAGE":{"3P":["general_zone"],"1P":["SANR","SANS","SURR","SANQ","S4LI"]},"HOMEIMPROVEMENT":{"3P":["general_zone"],"1P":["SANR","SANS","SURR","SANQ","S4LI"]},"HOMEANDKITCHEN":{"3P":["general_zone"],"1P":["SANR","SANS","SURR","SANQ","S4LI"]},"CRAFTSOFINDIA":{"3P":["general_zone"],"1P":["SANR","SANS","SURR","SANQ","S4LI"]},"WELLNESS":{"1P":["SF11","SF40","SX9A"]},"ELECTRONICS":{"3P":["electronics_zone","general_zone"],"1P":["SACU","R696","SE40","S0BN","R080","SK1M","Y344","SJ93","R396","S573","SLTY","V014","SLKO"]}},"region_code":{"BOOKS":["PANINDIABOOKS"],"CRAFTSOFINDIA":["PANINDIACRAFT"],"ELECTRONICS":["PANINDIADIGITAL"],"FASHION":["PANINDIAFASHION"],"FURNITURE":["PANINDIAFURNITURE"],"GROCERIES":["TXCF","PANINDIAGROCERIES"],"HOMEANDKITCHEN":["PANINDIAHOMEANDKITCHEN"],"HOMEIMPROVEMENT":["PANINDIAHOMEIMPROVEMENT"],"JEWELLERY":["PANINDIAJEWEL"],"LOCALSHOPS":["PANINDIALOCALSHOPS"],"PREMIUMFRUITS":["S575"],"SPORTSTOYSLUGGAGE":["PANINDIASTL"],"WELLNESS":["PANINDIAWELLNESS"]},"vertical_code":["LOCALSHOPS","GROCERIES","FASHION","JEWELLERY","PREMIUMFRUITS","BOOKS","FURNITURE","SPORTSTOYSLUGGAGE","HOMEIMPROVEMENT","HOMEANDKITCHEN","CRAFTSOFINDIA","WELLNESS","ELECTRONICS"]}',
    "pin": "400008",
    "pragma": "no-cache",
    "referer": "https://www.jiomart.com/all-category",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
}

#-----------------------
# Crawler Settings
#-----------------------
crawler_api_url = "https://www.jiomart.com/trex/search"
crawler_headers = {
    "accept": "*/*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "origin": "https://www.jiomart.com",
    "pragma": "no-cache",
    "referer": "https://www.jiomart.com/c/groceries",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
}

#-----------------------
# price API Settings
#----------------------
price_headers ={
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "pin": "400008",
    "pragma": "no-cache",
    "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
}

#-----------------------
# review API Settings
#----------------------
review_headers = {
    "accept": "application/json",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "access-control-allow-origin": "*",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "jwt-token": "null",
    "origin": "https://www.jiomart.com",
    "pragma": "no-cache",
    "referer": "https://www.jiomart.com/",
    "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "userid": "0",
    "vertical": "jiomart",
}

FILE_NAME = "jiomart_products.csv"

# Define CSV headers
# ------------------------
FILE_HEADERS = [
    "unique_id", "competitor_name", "store_name", "store_addressline1", "store_addressline2",
    "store_suburb", "store_state", "store_postcode", "store_addressid", "extraction_date",
    "product_name", "brand", "brand_type", "grammage_quantity", "grammage_unit", "drained_weight",
    "producthierarchy_level1", "producthierarchy_level2", "producthierarchy_level3",
    "producthierarchy_level4", "producthierarchy_level5", "producthierarchy_level6",
    "producthierarchy_level7", "regular_price", "selling_price", "price_was", "promotion_price",
    "promotion_valid_from", "promotion_valid_upto", "promotion_type", "percentage_discount",
    "promotion_description", "package_sizeof_sellingprice", "per_unit_sizedescription",
    "price_valid_from", "price_per_unit", "multi_buy_item_count", "multi_buy_items_price_total",
    "currency", "breadcrumb", "pdp_url", "variants", "product_description", "instructions",
    "storage_instructions", "preparationinstructions", "instructionforuse", "country_of_origin",
    "allergens", "age_of_the_product", "age_recommendations", "flavour", "nutritions",
    "nutritional_information", "vitamins", "labelling", "grade", "region", "packaging", "receipies",
    "processed_food", "barcode", "frozen", "chilled", "organictype", "cooking_part", "Handmade",
    "max_heating_temperature", "special_information", "label_information", "dimensions",
    "special_nutrition_purpose", "feeding_recommendation", "warranty", "color", "model_number",
    "material", "usp", "dosage_recommendation", "tasting_note", "food_preservation", "size",
    "rating", "review", "file_name_1", "image_url_1", "file_name_2", "image_url_2", "file_name_3",
    "image_url_3", "competitor_product_key", "fit_guide", "occasion", "material_composition",
    "style", "care_instructions", "heel_type", "heel_height", "upc", "features", "dietary_lifestyle",
    "manufacturer_address", "importer_address", "distributor_address", "vinification_details",
    "recycling_information", "return_address", "alchol_by_volume", "beer_deg", "netcontent",
    "netweight", "site_shown_uom", "ingredients", "random_weight_flag", "instock", "promo_limit",
    "product_unique_key", "multibuy_items_pricesingle", "perfect_match", "servings_per_pack",
    "Warning", "suitable_for", "standard_drinks", "grape_variety", "retail_limit"
]