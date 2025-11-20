from datetime import datetime
import os
import calendar
import logging
import configparser
import pytz
from dateutil.relativedelta import relativedelta, MO
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# basic details
PROJECT = "homecentre"
CLIENT_NAME = "homecentre"
PROJECT_NAME = "homecentre"
FREQUENCY = "daily"
BASE_URL = "https://www.homecentre.com/ae"

datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))
iteration = datetime_obj.strftime("%Y_%m_%d")
YEAR = datetime_obj.strftime("%Y")
MONTH = datetime_obj.strftime("%m")
DAY = datetime_obj.strftime("%d")
MONTH_VALUE = calendar.month_abbr[int(MONTH.lstrip("0"))]
WEEK = (int(DAY) - 1) // 7 + 1

FILE_NAME = f"homecentre_{iteration}.csv"

# Mongo db and collections
MONGO_DB = f"homecentre_ae_{iteration}"
MONGO_COLLECTION_PRODUCTS = f"{PROJECT_NAME}_url"
MONGO_COLLECTION_CATEGORY = f"{PROJECT_NAME}_category"
MONGO_COLLECTION_URL_FAILED = f"{PROJECT_NAME}_url_failed"
MONGO_COLLECTION_DATA = f"{PROJECT_NAME}_data"



HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Priority': 'u=0, i',
}

# Default headers used for homepage / product requests
HOMEPAGE_HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Headers for Algolia POST
ALGOLIA_HEADERS = {
    "Accept": "*/*",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://www.homecentre.com",
    "Referer": "https://www.homecentre.com/",
    "User-Agent": HOMEPAGE_HEADERS["user-agent"],
}

# Algolia / PLP API
API_URL = (
    "https://3hwowx4270-dsn.algolia.net/1/indexes/*/queries"
    "?X-Algolia-API-Key=4c4f62629d66d4e9463ddb94b9217afb"
    "&X-Algolia-Application-Id=3HWOWX4270"
    "&X-Algolia-Agent=Algolia%20for%20vanilla%20JavaScript%202.9.7"
)

# Pagination / limits
HITS_PER_PAGE = 42

# Misc
BASE_HOMEPAGE = "https://www.homecentre.com/ae"

FILE_HEADERS = [
    "url", "product_id", "product_name", "product_color", "material",
    "quantity", "details_string", "specification", "price", "wasprice",
    "product_type", "breadcrumb", "stock", "image"
]