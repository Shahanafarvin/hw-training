import logging
from datetime import datetime

BASE_URL = "https://www.mrosupply.com"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

MONGO_DB="mrosupply_db"
MONGO_COLLECTION_CATEGORY="categories"
MONGO_COLLECTION_PRODUCTS="products"
MONGO_COLLECTION_DATA="product_data"

FILE_NAME = f"mrosupply_products_export_{datetime.now().strftime('%Y%m%d')}.csv"

FILE_HEADERS = [
    "Company Name",
    "Manufacturer Name",
    "Brand Name",
    "Vendor/Seller Part Number",
    "Item Name",
    "Full Product Description",
    "Price",
    "Unit of Issue",
    "QTY Per UOI",
    "Product Category",
    "URL",
    "Availability",
    "Manufacturer Part Number",
    "Country of Origin",
    "UPC",
    "Model Number"
]