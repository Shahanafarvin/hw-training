import time
import random
from pathlib import Path
from curl_cffi import requests as curl_requests
from mongoengine import connect, disconnect
from items import CategoryTreeItem, ProductItem
from settings import (
    crawler_headers as headers,
    cookies,
    crawler_api_url as API_URL,
    MONGO_DB,
    MONGO_URI,
    logging,
)

# -----------------------------
# Load User Agents
# -----------------------------
try:
    ua_file = Path("/home/shahana/datahut-training/hw-training/user_agents.txt")
    USER_AGENTS = [u.strip() for u in ua_file.read_text().splitlines() if u.strip()]
    if not USER_AGENTS:
        raise ValueError("user_agents.txt is empty")
except Exception as e:
    logging.warning(f" Failed to load user_agents.txt: {e}")
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ]

# -----------------------------
# Crawler Class
# -----------------------------
class Crawler:
    """Crawler for Jiomart product extraction using curl_cffi"""

    def __init__(self):
        connect(db=MONGO_DB, host=MONGO_URI, alias="default")
        self.session = curl_requests.Session(impersonate="chrome120")
        logging.info(" MongoDB connected and curl_cffi session initialized.")

    def start(self):
        """Start crawling from MongoDB category collection"""
        try:
            categories = CategoryTreeItem.objects.only("category_name", "category_id", "sub_categories")
            logging.info(f" Loaded {len(categories)} categories from MongoDB.")
        except Exception as e:
            logging.error(f" Failed to load categories: {e}")
            return

        for cat in categories:
            self.walk(cat.to_mongo().to_dict(), parent_name="")

    def walk(self, node, parent_name=""):
        """Recursively walk through sub-categories"""
        name = node.get("category_name") or node.get("name", "")
        sub = node.get("sub_categories", {})
        full_path = (parent_name + " > " + name).strip(" >")

        if sub:
            for sub_name, sub_data in sub.items():
                self.walk(sub_data, full_path)
        else:
            cat_id = node.get("category_id") or node.get("id")
            if cat_id:
                logging.info(f"🛒 Crawling category: {full_path} (ID: {cat_id})")
                meta = {"category_name": full_path, "cat_id": cat_id}
                self.parse_item(meta)
            else:
                logging.warning(f" Skipping category '{full_path}' — no ID found.")

    def parse_item(self, meta):
        """Fetch and store product data for one category"""
        cat_id = meta["cat_id"]
        total = 0
        page = 1
        next_page_token = None

        payload_template = {
            "pageSize": 50,
            "facetSpecs": [
                {"facetKey": {"key": "brands"}, "limit": 500, "excludedFilterKeys": ["brands"]},
                {"facetKey": {"key": "categories"}, "limit": 500, "excludedFilterKeys": ["categories"]},
            ],
            "variantRollupKeys": ["variantId"],
            "branch": "projects/sr-project-jiomart-jfront-prod/locations/global/catalogs/default_catalog/branches/0",
            "pageCategories": [str(cat_id)],
            "orderBy": "attributes.popularity desc",
            "filter": (
                f'attributes.status:ANY("active") AND attributes.category_ids:ANY("{cat_id}") AND '
                '(attributes.available_regions:ANY("TXCF", "PANINDIAGROCERIES")) AND '
                '(attributes.inv_stores_1p:ANY("ALL", "T9V1") OR '
                'attributes.inv_stores_3p:ANY("ALL", "groceries_zone_non-essential_services", '
                '"general_zone", "groceries_zone_essential_services"))'
            ),
            "visitorId": "anonymous-3dea4a71-ffac-4226-97e4-0d853392d5e5",
        }

        while True:
            payload = payload_template.copy()
            if next_page_token:
                payload["pageToken"] = next_page_token

            headers["user-agent"] = random.choice(USER_AGENTS)
            logging.info(f" Fetching page {page} for category {cat_id}...")

            try:
                resp = self.session.post(
                    API_URL,
                    headers=headers,
                    cookies=cookies,
                    json=payload,
                    timeout=30,
                )

                if resp.status_code != 200:
                    logging.warning(f" HTTP {resp.status_code} for category {cat_id}, retrying...")
                    time.sleep(random.uniform(3, 7))
                    continue

                data = resp.json()
                results = data.get("results", [])
                count = len(results)
                total += count

                if count == 0:
                    logging.info(f" No products found for {meta['category_name']}")
                    break

                logging.info(f" Page {page}: {count} products extracted")

                for product in results:
                    variant = product.get("product", {}).get("variants", [{}])[0]
                    unique_id = variant.get("id", "")
                    if not unique_id:
                        continue

                    # Avoid duplicates
                    if ProductItem.objects(unique_id=unique_id).first():
                        continue

                    alt_ids = variant.get("attributes", {}).get("alternate_product_code", {}).get("text", [])
                    alt_ids = ", ".join(map(str, alt_ids)) if isinstance(alt_ids, list) else str(alt_ids)

                    item = ProductItem(
                        unique_id=str(unique_id),
                        brand=(variant.get("brands", [""])[0] if variant.get("brands") else ""),
                        title=variant.get("title", ""),
                        pdp_url=variant.get("uri", ""),
                        images=variant.get("images", []),
                        category_path=product.get("product", {}).get("categories", []),
                        alternate_ids=alt_ids,
                        food_type=variant.get("attributes", {}).get("food_type", {}).get("text", "")[0],
                       
                    )

                    try:
                        item.save()
                    except Exception as e:
                        logging.error(f" Error saving product {unique_id}: {e}")

                next_page_token = data.get("nextPageToken")
                if not next_page_token:
                    logging.info(f"Done: {meta['category_name']} → {total} products saved.")
                    break

                page += 1
                time.sleep(random.uniform(2, 5))

            except Exception as e:
                logging.error(f"Request failed for category {cat_id}: {e}")
                time.sleep(random.uniform(4, 8))
                continue

    def close(self):
        """Close MongoDB connection and session"""
        self.session.close()
        disconnect(alias="default")
        


# -----------------------------
# Run Crawler
# -----------------------------
if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()
