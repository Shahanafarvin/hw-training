import time
import random
import logging
import requests
from mongoengine import connect
from items import ProductItem
from settings import MONGO_URI, MONGO_DB, CRAWLER_HEADERS

# Connect to MongoDB
connect(db=MONGO_DB, host=MONGO_URI)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Helper: map detail type to API endpoint template
DETAIL_URLS = {
    "description": "https://auchan.hu/api/v2/cache/products/{product_id}/variants/{selectvalue}/details/description?hl=hu",
    "parameterList": "https://auchan.hu/api/v2/cache/products/{product_id}/variants/{selectvalue}/details/parameterList?hl=hu",
    "ingredients": "https://auchan.hu/api/v2/cache/products/{product_id}/variants/{selectvalue}/details/ingredients?hl=hu",
    "nutrition": "https://auchan.hu/api/v2/cache/products/{product_id}/variants/{selectvalue}/details/nutrition?hl=hu",
    "allergens": "https://auchan.hu/api/v2/cache/products/{product_id}/variants/{selectvalue}/details/allergensDetailed?hl=hu",
}

MAX_RETRIES = 3

def fetch_detail(url):
    """Fetch detail JSON with retries and random delay"""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=CRAWLER_HEADERS, timeout=15)
            logging.info(f"Requesting: {url} → Status Code: {response.status_code}")
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                logging.warning(f"401 Unauthorized for URL {url}, attempt {attempt}/{MAX_RETRIES}")
                time.sleep(random.uniform(3, 6))  # delay before retry
            else:
                logging.warning(f"{response.status_code} for URL {url}")
                return None
        except requests.RequestException as e:
            logging.error(f"Request failed for URL {url}: {e}")
            time.sleep(random.uniform(1, 3))
    logging.error(f"Failed after {MAX_RETRIES} retries for URL {url}")
    return None

def main():
    products = ProductItem.objects()  # Fetch all products saved by crawler
    logging.info(f"Total products to parse: {products.count()}")

    for p in products:
        updated_fields = {}
        for detail in p.details or []:
            if detail not in DETAIL_URLS:
                continue

            url = DETAIL_URLS[detail].format(product_id=p.product_id, selectvalue=p.selectvalue)
            data = fetch_detail(url)
            if not data:
                continue

            # Update fields based on detail type
            if detail == "description":
                updated_fields["description"] = data.get("description", "")
            elif detail == "parameterList":
                updated_fields["parameters"] = data.get("parameters", [])
            elif detail == "ingredients":
                updated_fields["ingredients"] = data.get("description", "")
            elif detail == "nutrition":
                updated_fields["nutrition"] = data.get("nutritions", {}).get("data", [])
            elif detail == "allergens":
                allergens = data.get("allergensDetailed", [])
                updated_fields["allergens"] = ",".join([a.get("name", "") for a in allergens if "name" in a])

            time.sleep(random.uniform(0.5, 1.5))  # polite delay between requests

        if updated_fields:
            ProductItem.objects(id=p.id).update_one(**{f"set__{k}": v for k, v in updated_fields.items()})
            logging.info(f"Updated product: {p.title}")

if __name__ == "__main__":
    main()
