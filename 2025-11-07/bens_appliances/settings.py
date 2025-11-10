from datetime import datetime
import logging
import pytz
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Project details
PROJECT_NAME = "bens_appliances"
BASE_URL = "https://bens-appliances.com"

# MongoDB configuration
datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))
iteration = datetime_obj.strftime("%Y_%m_%d")
MONGO_DB = f"{PROJECT_NAME}_{iteration}"
MONGO_COLLECTION_URLS = f"{PROJECT_NAME}_urls"
MONGO_COLLECTION_DATA = f"{PROJECT_NAME}_data"

# Headers
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/141.0.0.0 Safari/537.36"
    ),
}

#export config
FILE_HEADERS = [
        "url",
        "title",
        "manufacturer",
        "price",
        "description",
        "oem_part_number",
        "retailer_part_number",
        "competitor_part_numbers",
        "compatible_products",
        "equivalent_part_numbers",
        "product_specifications",
        "additional_description",
        "availability",
        "image_urls",
        "linked_files",
    ]

file_name = "bens_appliances.csv"
