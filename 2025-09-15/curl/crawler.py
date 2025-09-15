import logging
import psutil
import time
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from curl_cffi import requests
from lxml import html


class Carbon38Scraper:
    def __init__(self, start_url, mongo_uri="mongodb://localhost:27017/", db_name="carbon38", collection_name="curlcffi_url"):
        self.start_url = start_url
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.start_time = None

        # Logger setup
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(message)s",
            level=logging.INFO
        )
        self.logger = logging.getLogger(__name__)

    def connect_mongo(self):
        """Initialize MongoDB connection"""
        try:
            self.client = MongoClient(self.mongo_uri)
            db = self.client[self.db_name]
            self.collection = db[self.collection_name]
            self.logger.info("Connected to MongoDB successfully.")
        except PyMongoError as e:
            self.logger.error(f"MongoDB connection error: {e}")
            raise

    def save_to_mongo(self, data):
        """Save product URLs to MongoDB"""
        try:
            if data:
                self.collection.insert_many(data)
                self.logger.info(f"Inserted {len(data)} product URLs into MongoDB.")
        except PyMongoError as e:
            self.logger.error(f"MongoDB insert error: {e}")

    def scrape(self):
        """Scrape product URLs using curl_cffi + XPath"""
        self.connect_mongo()
        scraped_data = []
        self.start_time = time.time()

        current_url = self.start_url
        while current_url:
            try:
                self.logger.info(f"Scraping page: {current_url}")
                # curl_cffi will impersonate Chrome automatically
                resp = requests.get(current_url, impersonate="chrome", timeout=60)
                resp.raise_for_status()

                tree = html.fromstring(resp.text)

                # Extract product links using XPath
                product_links = tree.xpath('//a[contains(@class,"ProductItem__ImageWrapper")]/@href')
                if not product_links:
                    self.logger.warning(f"No product links found on {current_url}")
                else:
                    scraped_data.extend([{"product_url": "https://carbon38.com" + link} for link in product_links])
                    self.logger.info(f"Found {len(product_links)} product URLs.")

                # Check for next page using XPath
                next_page_list = tree.xpath('//a[contains(@class,"Pagination__NavItem") and @title="Next page"]/@href')
                current_url = next_page_list[0] if next_page_list else None
                if current_url and not current_url.startswith("http"):
                    current_url = "https://carbon38.com" + current_url

            except Exception as e:
                self.logger.error(f"Error scraping {current_url}: {e}")
                break

        # Save to MongoDB
        self.save_to_mongo(scraped_data)

        # Print efficiency summary
        self.print_efficiency()

    def print_efficiency(self):
        """Print overall running efficiency using psutil"""
        elapsed_time = time.time() - self.start_time
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()

        self.logger.info("===== SCRAPING EFFICIENCY =====")
        self.logger.info(f"Total time elapsed: {elapsed_time:.2f} seconds")
        self.logger.info(f"CPU usage: {cpu_percent}%")
        self.logger.info(f"Memory usage: {memory_info.percent}%")
        self.logger.info("================================")

    def close(self):
        if self.client:
            self.client.close()
            self.logger.info("MongoDB connection closed.")


if __name__ == "__main__":
    start_url = "https://www.carbon38.com/shop-all-activewear/tops"
    scraper = Carbon38Scraper(start_url)
    scraper.scrape()
    scraper.close()
