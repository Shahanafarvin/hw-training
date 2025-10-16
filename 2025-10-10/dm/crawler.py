import logging
import json
import requests
from pymongo import MongoClient, errors
from settings import HEADERS, MONGO_COLLECTION_CATEGORY, MONGO_DB

class Crawler:
    """Crawling product URLs from DM Austria"""

    def __init__(self):
        # MongoDB connection
        self.mongo = MongoClient("mongodb://localhost:27017/")
        self.db = self.mongo[MONGO_DB]
        self.collection = self.db[MONGO_COLLECTION_CATEGORY]
        self.collection.create_index("product_url", unique=True)

        # Base URLs
        self.base_url = "https://www.dm.at"
        self.api_base = "https://product-search.services.dmtech.com/at/search/static"

        self.inserted_count = 0
        self.skipped_count = 0

    def start(self):
        """Start crawling"""
        JSON_FILE = "/home/shahana/datahut-training/hw-training/2025-10-10/dm/dm_category_filters_sort.json"

        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                categories = json.load(f)
            logging.info(f"Loaded {len(categories)} categories from {JSON_FILE}")
        except FileNotFoundError:
            logging.error(f"Category file {JSON_FILE} not found.")
            return

        for cat in categories:
            filters = cat.get("filters")
            sort = cat.get("sort", "editorial_relevance")

            if not filters:
                continue

            filter_param = filters.replace(":", "=").replace(" ", "&")
            api = f"{self.api_base}?{filter_param}&pageSize=30&searchType=editorial-search&sort={sort}&type=search-static"

            logging.info(f"Processing category: {cat.get('category_path', '')}")
            logging.info(f"API: {api}")

            first_response = requests.get(f"{api}", headers=HEADERS)
            if first_response.status_code != 200:
                logging.warning(f"Failed initial page ({first_response.status_code}) → skipping category")
                continue

            first_json = first_response.json()
            total_products = first_json.get("count", 0)
            total_pages = first_json.get("totalPages", 1)
            logging.info(f"Found {total_products} products → {total_pages} pages")

            self.process_pages(api, total_pages, cat)

        self.summary()

    def process_pages(self, api, total_pages, cat):
        """Iterate through category pages and store product URLs"""
        category_inserted = 0
        category_skipped = 0

        for page in range(0, total_pages + 1):
            paginated_url = f"{api}&currentPage={page}"
            response = requests.get(paginated_url, headers=HEADERS)

            if response.status_code != 200:
                logging.warning(f"Failed page {page} ({response.status_code})")
                continue

            data = response.json()
            products = data.get("products", [])

            for product in products:
                gtin = product.get("gtin") or product.get("tileData", {}).get("gtin")
                product_path = product.get("tileData", {}).get("self")

                if gtin and product_path:
                    product_url = self.base_url + product_path
                    product_doc = {
                        "gtin": gtin,
                        "product_url": product_url,
                        "category_path": cat.get("category_path", "")
                    }

                    try:
                        result = self.collection.update_one(
                            {"product_url": product_url},
                            {"$setOnInsert": product_doc},
                            upsert=True
                        )
                        if result.upserted_id:
                            self.inserted_count += 1
                            category_inserted += 1
                        else:
                            self.skipped_count += 1
                            category_skipped += 1
                    except errors.DuplicateKeyError:
                        self.skipped_count += 1
                        category_skipped += 1

        logging.info(f"{cat.get('category_path', '')}: Inserted={category_inserted}, Skipped={category_skipped}")

    def summary(self):
        """Final summary of crawl results"""
        logging.info("Crawling completed successfully.")
        logging.info(f"Total Inserted: {self.inserted_count}")
        logging.info(f"Total Skipped (Duplicates): {self.skipped_count}")

    def close(self):
        """Close database connections"""
        self.mongo.close()


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()
