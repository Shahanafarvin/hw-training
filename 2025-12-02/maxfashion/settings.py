from datetime import datetime
import os
import calendar
import logging
import pytz

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Basic details
PROJECT = "dave"
CLIENT_NAME = "peter"
PROJECT_NAME = "maxfashion"
FREQUENCY = "POC"
BASE_URL = "https://www.maxfashion.com"
START_URL = "https://www.maxfashion.com/ae/en/"

# DateTime setup
datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))
iteration = datetime_obj.strftime("%Y_%m_%d")
YEAR = datetime_obj.strftime("%Y")
MONTH = datetime_obj.strftime("%m")
DAY = datetime_obj.strftime("%d")
MONTH_VALUE = calendar.month_abbr[int(MONTH.lstrip("0"))]
WEEK = (int(DAY) - 1) // 7 + 1

# MongoDB collections
MONGO_DB = f"maxfashion_2025_12_04"
MONGO_COLLECTION_CATEGORY = f"{PROJECT_NAME}_category_url"
MONGO_COLLECTION_PRODUCTS = f"{PROJECT_NAME}_product_url"
MONGO_COLLECTION_URL_FAILED = f"{PROJECT_NAME}_url_failed"
MONGO_COLLECTION_DATA = f"product_data_item"

# File settings
FILE_NAME = f"{PROJECT_NAME}_{YEAR}_{MONTH}_{DAY}_sample.csv"

HEADERS = {
    'accept': '*/*',
    'accept-language': 'en-US, en-US',
    'cache-control': 'no-cache',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
    'x-context-request': '{"applicationId":"mx-ae","tenantId":"5DF1363059675161A85F576D"}',
    'x-lmg-context-request': '{"lang":"en","platform":"Desktop"}',
    'x-price-context': '{"locale":"en","currency":"AED"}'
}

FILE_HEADERS = [
    "unique_id",
    "url",
    "product_name",
    "product_details",
    "color",
    "quantity",
    "size",
    "selling_price",
    "regular_price",
    "image",
    "description",
    "currency",
    "gender",
    "breadcrumbs",
    "extraction_date"
]