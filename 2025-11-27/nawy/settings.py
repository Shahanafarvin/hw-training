from datetime import datetime
import calendar
import logging
import pytz

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# basic details
PROJECT = "Property Manager"
CLIENT_NAME = "Peter"
PROJECT_NAME = "nawy"
FREQUENCY = "POC"
BASE_URL = "https://www.nawy.com/"


datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))

iteration = datetime_obj.strftime("%Y_%m_%d")
YEAR = datetime_obj.strftime("%Y")
MONTH = datetime_obj.strftime("%m")
DAY = datetime_obj.strftime("%d")
MONTH_VALUE = calendar.month_abbr[int(MONTH.lstrip("0"))]
WEEK = (int(DAY) - 1) // 7 + 1

FILE_NAME = f"nawy_{iteration}.csv"

# Mongo db and collections
MONGO_DB = f"nawy_{iteration}"
MONGO_COLLECTION_URLS= f"{PROJECT_NAME}_url"
MONGO_COLLECTION_URL_FAILED = f"{PROJECT_NAME}_url_failed"
MONGO_COLLECTION_DATA = f"{PROJECT_NAME}_data"


HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en",
    "cache-control": "no-cache",
    "client-id": "5vCTlhIIEr",
    "content-type": "application/json",
    "origin": "https://www.nawy.com",
    "platform": "web",
    "pragma": "no-cache",
    "referer": "https://www.nawy.com/",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
}

proxies={
        "http": "http://fauchjoh:k46ta12me1wb@142.111.48.253:7030/",
        "https": "http://fauchjoh:k46ta12me1wb@142.111.48.253:7030/"
    }

# API Configuration
API_URL = "https://webapi.nawy.com/api/properties/search?token=undefined&language=en&client_id=LObZQx8rno"


FILE_HEADER = [
    "id",
    "reference_number",
    "url",
    "broker_display_name",
    "broker",
    "category",
    "category_url",
    "title",
    "description",
    "location",
    "price",
    "currency",
    "price_per",
    "bedrooms",
    "bathrooms",
    "furnished",
    "rera_permit_number",
    "dtcm_licence",
    "scraped_ts",
    "amenities",
    "details",
    "agent_name",
    "number_of_photos",
    "user_id",
    "phone_number",
    "date",
    "iteration_number",
    "depth",
    "property_type",
    "sub_category_1",
    "sub_category_2",
    "published_at",
]
