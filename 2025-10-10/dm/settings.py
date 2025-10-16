import calendar
import logging
from datetime import datetime
import pytz


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
# DATE AND TIME VARIABLES
# -------------------------------------------------
datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))
iteration = datetime_obj.strftime("%Y_%m_%d")
YEAR = datetime_obj.strftime("%Y")
MONTH = datetime_obj.strftime("%m")
DAY = datetime_obj.strftime("%d")
MONTH_VALUE = calendar.month_abbr[int(MONTH.lstrip("0"))]
WEEK = (int(DAY) - 1) // 7 + 1

FILE_NAME = f"{PROJECT_NAME}_{iteration}"

# -------------------------------------------------
# MONGO DB AND COLLECTIONS
# -------------------------------------------------
MONGO_DB = f"{PROJECT_NAME}_{iteration}"
MONGO_COLLECTION_CATEGORY = "product_url"
MONGO_COLLECTION_DATA = "product_details"



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
