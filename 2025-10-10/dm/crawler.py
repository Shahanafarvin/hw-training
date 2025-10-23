import logging
import requests
from mongoengine import connect, errors
from items import ProductCategoryUrlItem, ProductUrlItem
from settings import HEADERS, MONGO_DB

class Crawler:
    """Crawling product URLs from DM Austria using MongoEngine"""

    def __init__(self):
        # MongoEngine connection
        connect(db=MONGO_DB, alias="default", host="localhost", port=27017)

        # Base URLs
        self.base_url = "https://www.dm.at"
        self.api_base = "https://product-search.services.dmtech.com/at/search/static"

        self.inserted_count = 0
        self.skipped_count = 0

    def start(self):
        """Start crawling categories from MongoDB"""
        categories = ProductCategoryUrlItem.objects()  # fetch all categories from MongoDB
        logging.info(f"Loaded {categories.count()} categories from MongoDB")

        for cat in categories:
            if not cat.filters:
                continue

            filter_param = cat.filters.replace(":", "=").replace(" ", "&")
            sort = cat.sort or "editorial_relevance"
            api = f"{self.api_base}?{filter_param}&pageSize=30&searchType=editorial-search&sort={sort}&type=search-static"

            logging.info(f"Processing category: {cat.category_path}")
            logging.info(f"API: {api}")

            try:
                first_response = requests.get(api, headers=HEADERS)
                first_response.raise_for_status()
            except requests.RequestException as e:
                logging.warning(f"Failed initial request → skipping category: {e}")
                continue

            first_json = first_response.json()
            total_products = first_json.get("count", 0)
            total_pages = first_json.get("totalPages", 1)
            logging.info(f"Found {total_products} products → {total_pages} pages")

            self.process_pages(api, total_pages, cat)

        logging.info(f"Total Inserted: {self.inserted_count}")
        logging.info(f"Total Skipped (Duplicates): {self.skipped_count}")

    def process_pages(self, api, total_pages, cat):
        """Iterate through category pages and store product URLs"""
        category_inserted = 0
        category_skipped = 0

        for page in range(0, total_pages + 1):
            paginated_url = f"{api}&currentPage={page}"
            try:
                response = requests.get(paginated_url, headers=HEADERS)
                response.raise_for_status()
            except requests.RequestException:
                logging.warning(f"Failed page {page} → skipping")
                continue

            data = response.json()
            products = data.get("products", [])

            for product in products:
                gtin = product.get("gtin") or product.get("tileData", {}).get("gtin")
                product_path = product.get("tileData", {}).get("self")

                if not (gtin and product_path):
                    continue

                product_url = self.base_url + product_path
                product_doc = ProductUrlItem(
                    url=product_url,
                    gtin=int(gtin),
                    category_path=cat.category_path
                )

                try:
                    product_doc.save(force_insert=True)  # raises NotUniqueError if duplicate
                    self.inserted_count += 1
                    category_inserted += 1
                except errors.NotUniqueError:
                    self.skipped_count += 1
                    category_skipped += 1

        logging.info(f"{cat.category_path}: Inserted={category_inserted}, Skipped={category_skipped}")


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
