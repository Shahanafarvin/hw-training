from datetime import datetime
import logging
import pytz

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

PROJECT_NAME = "stlouis_carmuseum"

datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))
iteration = datetime_obj.strftime("%Y_%m_%d")

FILE_NAME = f"{PROJECT_NAME}_{iteration}.csv"

# MongoDB settings
MONGO_DB = f"{PROJECT_NAME}_{iteration}"
MONGO_COLLECTION_DATA = f"{PROJECT_NAME}_data"
MONGO_COLLECTION_URLS = f"{PROJECT_NAME}_urls"

# Queue placeholder
QUEUE = ""

# Headers
HEADERS = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "origin": "https://www.stlouiscarmuseum.com",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
}

# CSV Headers
FILE_HEADERS = [
    "make", "model", "year", "VIN", "price", "mileage",
    "transmission", "engine", "color", "fuel_type", "body_style",
    "description", "image_URLs","source_link"
]