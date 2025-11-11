import logging
import calendar
from datetime import datetime
import pytz
from mongoengine import connect

# ---------- Project config ----------
PROJECT_NAME = "ereplacementparts"
BASE_URL = "https://www.ereplacementparts.com"

# ---------- Date / iteration ----------
datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))
iteration = datetime_obj.strftime("%Y_%m_%d")
YEAR = datetime_obj.strftime("%Y")
MONTH = datetime_obj.strftime("%m")
DAY = datetime_obj.strftime("%d")
MONTH_VALUE = calendar.month_abbr[int(MONTH.lstrip("0"))]

# ---------- MongoDB ----------
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = f"{PROJECT_NAME}_{iteration}"

# collection names (strings used by mongoengine meta)
MONGO_COLLECTION_CATEGORY = f"{PROJECT_NAME}_categories"
MONGO_COLLECTION_PRODUCT_URLS = f"{PROJECT_NAME}_product_urls"
MONGO_COLLECTION_PRODUCT_DETAILS = f"{PROJECT_NAME}_product_details"

# connect mongoengine
MONGO_CONNECTION=connect(db=MONGO_DB, host=MONGO_URI)

# ---------- Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ---------- HTTP headers ----------
HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Origin": "https://www.ereplacementparts.com",
    "Pragma": "no-cache",
    "Priority": "u=1, i",
    "Referer": "https://www.ereplacementparts.com/",
    "Sec-CH-UA": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Linux"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
}

# polite delay
REQUEST_DELAY = 1.5

# export config
FILE_NAME = "ereplacementparts_products.csv"

FILE_HEADERS = [
        "URL",
        "Product Name",
        "Price",
        "currency",
        "OEM Part For",
        "Part Number",
        "Availability",
        "Breadcrumbs",
        "Description",
        "Additional Description",
    ]