import logging
from datetime import datetime


# -------------------------------------------------
# LOGGING CONFIGURATION
# -------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# -------------------------------------------------
# BASIC PROJECT DETAILS
# -------------------------------------------------
PROJECT = "dm_austria"
CLIENT_NAME = "DM"
PROJECT_NAME = "dm_austria"
FREQUENCY = "N/A"
BASE_URL = "https://www.dm.at/"

# -------------------------------------------------
# MONGO DB AND COLLECTIONS
# -------------------------------------------------
MONGO_DB = "dm_austria_2025_10_16"
MONGO_COLLECTION_CATEGORY = "category_filters"
MONGO_COLLECTION_URLS = "product_url"
MONGO_COLLECTION_DATA = "product_details"

# -------------------------------------------------
# HEADERS FOR  CATEGORY API EXTRACTION
# -------------------------------------------------
CATEGORY_HEADERS = {
    "accept": "application/json",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "origin": "https://www.dm.at",
    "pragma": "no-cache",
    "referer": "https://www.dm.at/",
    "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
}

# HEADERS AND USER AGENT
# -------------------------------------------------
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "origin": "https://www.dm.at",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://www.dm.at/",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "x-dm-product-search-tags": "presentation:grid;search-type:editorial;channel:web;editorial-type:category",
    "x-dm-product-search-token": "47522169265995"
}

# EXPORT FILENAM
# ------------------------
file_name = f"DataHut_Austria_{CLIENT_NAME}_FullDump_{datetime.now().strftime('%Y%m%d')}.csv"

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
