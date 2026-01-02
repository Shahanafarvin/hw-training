from datetime import datetime
import calendar
import logging
#import pytz

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# basic details
PROJECT = "women dresses"
CLIENT_NAME = ""
PROJECT_NAME = "mmlafleur"
FREQUENCY = "n/a" 
BASE_URL = "https://mmlafleur.com"


#datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))

# iteration = datetime_obj.strftime("%Y_%m_%d")
# YEAR = datetime_obj.strftime("%Y")
# MONTH = datetime_obj.strftime("%m")
# DAY = datetime_obj.strftime("%d")
# MONTH_VALUE = calendar.month_abbr[int(MONTH.lstrip("0"))]
# WEEK = (int(DAY) - 1) // 7 + 1

#FILE_NAME = f"{PROJECT_NAME}_{iterat"

# Mongo db and collections
MONGO_DB = f"{PROJECT_NAME}_2026_01_03"
MONGO_COLLECTION_PRODUCTS = f"{PROJECT_NAME}_products"
MONGO_COLLECTION_CATEGORY = f"{PROJECT_NAME}_category"
MONGO_COLLECTION_URL_FAILED = f"{PROJECT_NAME}_url_failed"
MONGO_COLLECTION_DATA = f"{PROJECT_NAME}_data"

