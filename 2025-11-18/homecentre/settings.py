import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s"
)

# Mongo
MONGO_DB = "homecentre_ae"
MONGO_CATEGORY_COLLECTION="categories"
MONGO_PRODUCTS_COLLECTION="products"
MONGO_DATA_COLLECTION="full_data"

# Algolia / PLP API
API_URL = (
    "https://3hwowx4270-dsn.algolia.net/1/indexes/*/queries"
    "?X-Algolia-API-Key=4c4f62629d66d4e9463ddb94b9217afb"
    "&X-Algolia-Application-Id=3HWOWX4270"
    "&X-Algolia-Agent=Algolia%20for%20vanilla%20JavaScript%202.9.7"
)

# Default headers used for homepage / product requests
HOMEPAGE_HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Headers for Algolia POST
ALGOLIA_HEADERS = {
    "Accept": "*/*",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://www.homecentre.com",
    "Referer": "https://www.homecentre.com/",
    "User-Agent": HOMEPAGE_HEADERS["user-agent"],
}

# Pagination / limits
HITS_PER_PAGE = 42

# Misc
BASE_HOMEPAGE = "https://www.homecentre.com/ae"

FILE_HEADERS = [
    "url", "product_id", "product_name", "product_color", "material",
    "quantity", "details_string", "specification", "price", "wasprice",
    "product_type", "breadcrumb", "stock", "image"
]

FILE_NAME= "homecentre.csv"
