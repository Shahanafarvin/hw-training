from datetime import datetime
import logging
import pytz
import calendar

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ==========================
# Project Details
# ==========================
PROJECT = "auchan"
CLIENT_NAME = "Auchan"
PROJECT_NAME = "auchan"
BASE_URL = "https://auchan.hu/"

# ==========================
# Timestamp & File Naming
# ==========================
datetime_obj = datetime.now(pytz.timezone("Europe/Budapest"))

iteration = datetime_obj.strftime("%Y_%m_%d")
YEAR = datetime_obj.strftime("%Y")
MONTH = datetime_obj.strftime("%m")
DAY = datetime_obj.strftime("%d")
MONTH_VALUE = calendar.month_abbr[int(MONTH.lstrip("0"))]
WEEK = (int(DAY) - 1) // 7 + 1

FILE_NAME = f"{PROJECT}_{iteration}.csv"

# ==========================
# MongoDB Configuration
# ==========================
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "Auchan"
MONGO_COLLECTION_CATEGORY = f"{PROJECT_NAME}_categories"
MONGO_COLLECTION_DATA = f"{PROJECT_NAME}_products"

# ==========================
# Headers for Requests
# ==========================
HEADERS = {
    "accept": "application/json",
    "accept-language": "hu",
    "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI4cG1XclQzWmxWMUFJbXdiMUhWYWE5T1BWSzkzcjhIcyIsImp0aSI6IjgwOTk3M2ZlNzAyNzYzMGE1ZTZkZjQ5MjQ5MmRhNmE0MjhhYzNhNTk1ZmViNTRhYzI2NDI2Y2MxZDdkNzdjNzgzMjc5ZjMxYmJkMWQ2NjFmIiwiaWF0IjoxNzYxMDIzMDY1LjMzOTkzMywibmJmIjoxNzYxMDIzMDY1LjMzOTkzNiwiZXhwIjoxNzYxMTA5NDY1LjMxNTQxLCJzdWIiOiJhbm9uXzNjNTkxZjM4LTMyNDItNDJjOS04ZTNmLTZmNjgwYTJkOTEzOSIsInNjb3BlcyI6W119.k1quA-b6_p1rNqYs7Y4hhRRPqz2rICfjSAb8dEJZoOp46njyn0gpjPyIq_533jTmDjyxMWrzkGxyxjd1E0xKUPGDu461_DRdzQ97SnEEISuaRGXrztymIjN43OZ4K2VLO1sx3rH3T50sB9_Y5kUSYJPgvxLHikzCzWMe9fAKrzX65xmA4JbPiXhKxo58SF-izGgCHHekNyCu2pDXf9Qqa4g_Npc2CzEGcr24RyPY6zwGDA-0G_jTeKO9WfjuZcrXH5ZAtQjbUp0tJ6pUXiS9-07rJvcCS5eEPjoX2uz0enQJk9hKp4gquDaA88GzCBYSzqBAS81jyaLZmI_okdymzQ",  # Add token here
    "cache-control": "no-cache",
    "referer": BASE_URL,
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
}

CRAWLER_HEADERS = {
    "accept": "application/json",
    "accept-language": "hu",
    "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI4cG1XclQzWmxWMUFJbXdiMUhWYWE5T1BWSzkzcjhIcyIsImp0aSI6IjM3MTRkMzhlNTliMzJlMmIzMzNiMDhhYjk2M2U2Y2QwZTM3YTQwOWI5NDM3YmNhZDZjNjRlMDdmNmFiMTUwMGFmM2E0NTUxOGMxMjJjMWIyIiwiaWF0IjoxNzYxMjE5NzA3Ljc5ODU0NiwibmJmIjoxNzYxMjE5NzA3Ljc5ODU0OCwiZXhwIjoxNzYxMzA2MTA3Ljc3NjIxMywic3ViIjoiYW5vbl82YWI0MGM3Zi1hZjNjLTRkMWItOWQwNy0wYzk1MDU0N2Q1ZjkiLCJzY29wZXMiOltdfQ.Rx9npOZNknzGPUqrVx7IJ2Q3hIoXKJttBWMAmjfjNbv799JWHEzFtWauJrfyEV027jkballQjGcf2xqDOi1YlvisFu1pD0kA7wzWJU0AfV3_GnlhHwBwpeKWqt_tYZtylIYo28i9A7_mbgNfxWQp5KCu5LV7Smem7SAyDWlVto7aqUtouAGHvb0PI9_2fE4YYq8h1COTzUcPjNosS1lfqShyuyL-DUUfme7oziPcmUftdFsgFZ0ir7dTwI279ZPW1XJpExJKsezydfOEQQpC2ilrGxUcfFjCjjyBSBwGtDq0Gxw8GwiW7hCiSd7VSeAwEs2bG_TR-7MzzKw9vWLAaA",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
}


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

