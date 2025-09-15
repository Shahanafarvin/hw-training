import logging
import psutil
from playwright.sync_api import sync_playwright
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import time


class Carbon38Scraper:
    def __init__(self, start_url, mongo_uri="mongodb://localhost:27017/", db_name="carbon38", collection_name="playwright_url"):
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
        """Scrape product URLs using Playwright with XPath"""
        self.connect_mongo()
        scraped_data = []
        self.start_time = time.time()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            current_url = self.start_url
            while current_url:
                try:
                    page.goto(current_url, timeout=60000)
                    self.logger.info(f"Scraping page: {current_url}")

                    # Extract product links using XPath
                    product_elements = page.query_selector_all(
                        '//a[@class="ProductItem__ImageWrapper ProductItem__ImageWrapper--withAlternateImage"]'
                    )
                    product_links = [el.get_attribute("href") for el in product_elements]

                    if not product_links:
                        self.logger.warning(f"No product links found on {current_url}")
                    else:
                        scraped_data.extend([{"product_url": "https://carbon38.com"+link} for link in product_links])
                        self.logger.info(f"Found {len(product_links)} product URLs.")

                    # Check for next page using XPath
                    next_page_el = page.query_selector(
                        '//a[@class="Pagination__NavItem Link Link--primary" and @title="Next page"]'
                    )
                    next_page = next_page_el.get_attribute("href") if next_page_el else None
                    current_url = next_page if next_page else None

                except Exception as e:
                    self.logger.error(f"Error scraping {current_url}: {e}")
                    break

            browser.close()

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
