import logging
import psutil
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient
from pymongo.errors import PyMongoError


class Carbon38ScraperSelenium:
    def __init__(self, start_url, mongo_uri="mongodb://localhost:27017/", db_name="carbon38", collection_name="selenium_url"):
        self.start_url = start_url
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.start_time = None
        self.driver = None

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

    def setup_driver(self, headless=True):
        """Setup Selenium Chrome driver"""
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def scrape(self):
        """Scrape product URLs using Selenium with XPath"""
        self.connect_mongo()
        self.setup_driver(headless=True)
        scraped_data = []
        self.start_time = time.time()

        current_url = self.start_url
        while current_url:
            try:
                self.driver.get(current_url)
                self.logger.info(f"Scraping page: {current_url}")

                # Extract product links using XPath
                product_elements = self.driver.find_elements(By.XPATH,
                    '//a[@class="ProductItem__ImageWrapper ProductItem__ImageWrapper--withAlternateImage"]'
                )
                product_links = [el.get_attribute("href") for el in product_elements]

                if not product_links:
                    self.logger.warning(f"No product links found on {current_url}")
                else:
                    scraped_data.extend([{"product_url": link} for link in product_links])
                    self.logger.info(f"Found {len(product_links)} product URLs.")

                # Check for next page using XPath
                try:
                    next_page_el = self.driver.find_element(By.XPATH,
                        '//a[@class="Pagination__NavItem Link Link--primary" and @title="Next page"]'
                    )
                    next_page = next_page_el.get_attribute("href")
                    current_url = next_page if next_page else None
                except NoSuchElementException:
                    current_url = None

            except TimeoutException as e:
                self.logger.error(f"Timeout scraping {current_url}: {e}")
                break
            except Exception as e:
                self.logger.error(f"Error scraping {current_url}: {e}")
                break

        self.driver.quit()

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
    scraper = Carbon38ScraperSelenium(start_url)
    scraper.scrape()
    scraper.close()
