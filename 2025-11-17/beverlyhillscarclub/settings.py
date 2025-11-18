import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s"
)

# MongoDB
MONGO_DB = "beverly_hills_car_club"
MONGO_COLL_URLS = "urls"
MONGO_COLL_DATA = "data"

# PLP API
BASE_URL = "https://www.beverlyhillscarclub.com/isapi_xml.php"

HEADERS = {
    "accept": "*/*",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
    "referer": "https://www.beverlyhillscarclub.com/inventory.htm?page_no=2:60&orderby=make,year",
}

LIMIT = 60
MAX_CARS = 473

FILE_NAME="beverlyhillscarclub.csv"

# CSV Headers
FILE_HEADERS = [
    "make", "model", "year", "VIN", "price", "mileage",
    "transmission", "engine", "color", "fuel_type", "body_style",
    "description", "image_URLs","source_link"
]
