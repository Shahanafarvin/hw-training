from datetime import datetime
import calendar
import logging
import pytz

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Basic project details
PROJECT = "gatewayclassiccars"
CLIENT_NAME = "gatewayclassiccars"
PROJECT_NAME = "gatewayclassiccars"
FREQUENCY = "N/A"
BASE_URL = "https://www.gatewayclassiccars.com/"

# Date-time setup
datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))
iteration = datetime_obj.strftime("%Y_%m_%d")
YEAR = datetime_obj.strftime("%Y")
MONTH = datetime_obj.strftime("%m")
DAY = datetime_obj.strftime("%d")
MONTH_VALUE = calendar.month_abbr[int(MONTH.lstrip("0"))]
WEEK = (int(DAY) - 1) // 7 + 1

FILE_NAME = f"{PROJECT_NAME}_{iteration}.csv"

# MongoDB Collections
MONGO_DB = f"{PROJECT_NAME}_{iteration}"
MONGO_COLLECTION_URLS = f"{PROJECT_NAME}_category_url"
MONGO_COLLECTION_DATA = f"{PROJECT_NAME}_data"

FILE_HEADERS = [
    "make",
    "model",
    "year",
    "vin",
    "price",
    "mileage",
    "transmission",
    "engine",
    "color",
    "fuel type",
    "body style",
    "description",
    "image URLs",
    "source link",
]
