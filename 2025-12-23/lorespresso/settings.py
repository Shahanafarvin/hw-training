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
PROJECT = "ecommerce"
CLIENT_NAME = "Zan Reed"
PROJECT_NAME = "lorespresso"
FREQUENCY = "other"
BASE_URL = "https://www.lorespresso.com/en_gb"


datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))

iteration = datetime_obj.strftime("%Y_%m_%d")
YEAR = datetime_obj.strftime("%Y")
MONTH = datetime_obj.strftime("%m")
DAY = datetime_obj.strftime("%d")
MONTH_VALUE = calendar.month_abbr[int(MONTH.lstrip("0"))]
WEEK = (int(DAY) - 1) // 7 + 1

FILE_NAME = f"{PROJECT_NAME}_{iteration}"

# Mongo db and collections
MONGO_DB = f"{PROJECT_NAME}_2025_12_25"
MONGO_COLLECTION_PRODUCTS = f"{PROJECT_NAME}_products"
MONGO_COLLECTION_CATEGORY = f"{PROJECT_NAME}_category"
MONGO_COLLECTION_URL_FAILED = f"{PROJECT_NAME}_url_failed"
MONGO_COLLECTION_DATA = f"{PROJECT_NAME}_data"

# Request headers
headers = {
            "sec-ch-ua-platform": '"Linux"',
            "Referer": "https://www.lorespresso.com/en_gb",
            "purpose": "prefetch",
            "x-middleware-prefetch": "1",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "newrelic": "eyJ2IjpbMCwxXSwiZCI6eyJ0eSI6IkJyb3dzZXIiLCJhYyI6IjYyODQwMTAiLCJhcCI6IjE1ODkwNDU5NzgiLCJpZCI6ImMyOWMzZDgyOTNmNGNlMTgiLCJ0ciI6ImEzYTBhM2E0MWY2ZjVhNTViMzA2Y2RkMDMxYWYzNDVhIiwidGkiOjE3NjY0ODIxMTY5NDl9fQ==",
            "sec-ch-ua-mobile": "?0",
            "request-id": "|56746b154b7a4b69b346477e6c743a7c.9be46b34e9c6468e",
            "x-nextjs-data": "1",
            "traceparent": "00-a3a0a3a41f6f5a55b306cdd031af345a-c29c3d8293f4ce18-01",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "tracestate": "6284010@nr=0-1-6284010-1589045978-c29c3d8293f4ce18----1766482116949"
        }