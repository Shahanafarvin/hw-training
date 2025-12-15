from datetime import datetime
import calendar
import logging
import pytz

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),               # terminal
        logging.FileHandler("farmaline_scraping.log")     # file
    ]
)

# Basic details
PROJECT = "pharma_com"
CLIENT_NAME = "pharma_com"
PROJECT_NAME = "farmaline"
FREQUENCY = "N/A"
BASE_URL = "https://www.farmaline.be"


# DateTime setup
datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))
iteration = datetime_obj.strftime("%Y_%m_%d")
YEAR = datetime_obj.strftime("%Y")
MONTH = datetime_obj.strftime("%m")
DAY = datetime_obj.strftime("%d")
MONTH_VALUE = calendar.month_abbr[int(MONTH.lstrip("0"))]
WEEK = (int(DAY) - 1) // 7 + 1

# MongoDB collections
MONGO_DB = f"{PROJECT_NAME}_db"
MONGO_COLLECTION_INPUT ="input"
MONGO_COLLECTION_PRODUCTS = f"{PROJECT_NAME}_products"
MONGO_COLLECTION_URL_FAILED = f"{PROJECT_NAME}_url_failed"
MONGO_COLLECTION_DATA = f"product_data_item"


# File settings
FILE_NAME = f"{PROJECT_NAME}_{YEAR}_{MONTH}_{DAY}_.csv"


