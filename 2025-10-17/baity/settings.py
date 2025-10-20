# settings.py
import logging
from datetime import datetime
import pytz
import calendar


# -----------------------------------------------------------
# Logging
# -----------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# -----------------------------------------------------------
# Basic Details
# -----------------------------------------------------------
PROJECT = "baity"
PROJECT_NAME = "baity_properties"
FREQUENCY = "daily"
BASE_URL = "https://baity.bh/properties/"

# -----------------------------------------------------------
#  Date Info
# -----------------------------------------------------------
datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))
iteration = datetime_obj.strftime("%Y_%m_%d")
YEAR = datetime_obj.strftime("%Y")
MONTH = datetime_obj.strftime("%m")
DAY = datetime_obj.strftime("%d")
MONTH_VALUE = calendar.month_abbr[int(MONTH.lstrip('0'))]
WEEK = (int(DAY) - 1) // 7 + 1

# -----------------------------------------------------------
# File Naming
# -----------------------------------------------------------
FILE_NAME = f"{PROJECT_NAME}_{iteration}"

# -----------------------------------------------------------
# Mongo Configuration
# -----------------------------------------------------------
MONGO_DB = f"{PROJECT_NAME}_{iteration}"
MONGO_COLLECTION_URL = f"{PROJECT_NAME}_url"


# -----------------------------------------------------------
# Headers
# -----------------------------------------------------------
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://baity.bh/properties/",
    "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "x-fingerprint": "fce5a48cac25c7fe959605720b5e56af",
    "x-requested-with": "XMLHttpRequest",
}

# -----------------------------------------------------------
# API Endpoint
# -----------------------------------------------------------
API_ENDPOINT = (
    "https://baity.bh/properties/map?"
    "search=&governorateChanged=0&min_latitude=25.82208398833634&"
    "max_latitude=26.346900072646612&min_longitude=50.29025870287133&"
    "max_longitude=50.88489371263695&zoom=11&baity_verified=0&"
    "virtual_tour=0&has_offer=0&filterCount=0&show_recomended=1&page={page}"
)
