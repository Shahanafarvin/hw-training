import logging
import psutil
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient
from pymongo.errors import PyMongoError


class Carbon38ProductParserSelenium:
    def __init__(self, mongo_uri="mongodb://localhost:27017/", db_name="carbon38",
                 url_collection="selenium_url", product_collection="selenium_data"):
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.url_collection_name = url_collection
        self.product_collection_name = product_collection
        self.client = None
        self.db = None
        self.url_collection = None
        self.product_collection = None
        self.start_time = None
        self.driver = None

        # Logger setup
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(message)s",
            level=logging.INFO
        )
        self.logger = logging.getLogger(__name__)

    def connect_mongo(self):
        """Connect to MongoDB and collections"""
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.db_name]
            self.url_collection = self.db[self.url_collection_name]
            self.product_collection = self.db[self.product_collection_name]
            self.logger.info("Connected to MongoDB successfully.")
        except PyMongoError as e:
            self.logger.error(f"MongoDB connection error: {e}")
            raise

    def fetch_product_urls(self):
        """Fetch product URLs from MongoDB"""
        try:
            urls = self.url_collection.find({}, {"_id": 0, "product_url": 1})
            return [u["product_url"] for u in urls]
        except PyMongoError as e:
            self.logger.error(f"Error fetching URLs from MongoDB: {e}")
            return []

    def save_product_data(self, data):
        """Save a single product data to MongoDB"""
        try:
            if data:
                self.product_collection.insert_one(data)
                self.logger.info(f"Saved product: {data.get('url')}")
        except PyMongoError as e:
            self.logger.error(f"Error inserting product data: {e}")

    def setup_driver(self, headless=True):
        """Setup Selenium Chrome driver"""
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def safe_get(self, url, timeout=30):
        """Load a page with timeout, stop if it takes too long"""
        self.driver.set_page_load_timeout(timeout)
        try:
            self.driver.get(url)
        except TimeoutException:
            self.logger.warning(f"Timeout loading {url}, stopping load...")
            self.driver.execute_script("window.stop();")

    def get_text_or_empty(self, xpath, wait_time=5, attr=None):
        """Return text or attribute for an element, else empty string"""
        try:
            el = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return el.get_attribute(attr).strip() if attr else el.text.strip()
        except Exception:
            return ""

    def parse_product_page(self, url):
        """Extract detailed product information from a product URL"""
        try:
            self.safe_get(url)

            # --- Extract fields ---
            brand_text = self.get_text_or_empty('//h2[contains(@class,"ProductMeta__Vendor")]/a')
            name_text = self.get_text_or_empty('//h1[contains(@class,"ProductMeta__Title")]')
            color_text = self.get_text_or_empty('//span[contains(@class,"ProductForm__SelectedValue")]')
            price_text = self.get_text_or_empty('//span[contains(@class,"ProductMeta__Price")]').replace("$", "").replace("USD", "").strip()

            # Sizes
            size_elements = self.driver.find_elements(By.XPATH, '//input[contains(@class,"SizeSwatch__Radio")]')
            size_list = [s.get_attribute("value") for s in size_elements if s.get_attribute("value")]

            # FAQ sections
            faq_elements = self.driver.find_elements(By.XPATH, '//div[contains(@class,"Faq__AnswerWrapper")]//p')
            editor_notes = faq_elements[0].get_attribute("innerHTML").strip() if len(faq_elements) > 0 else ""
            size_fit = faq_elements[1].get_attribute("innerHTML").strip() if len(faq_elements) > 1 else ""

            # Fabric & care
            fabric_care_text = ""
            try:
                fabric_care_el = self.driver.find_element(By.XPATH, '//div[contains(@class,"Faq__AnswerWrapper")]//p/span')
                raw_html = fabric_care_el.get_attribute("innerHTML")
                fabric_care_text = re.sub(r'<br\s*/?>', '\n', raw_html)
                fabric_care_text = re.sub(r'<[^>]+>', '', fabric_care_text).strip()
            except NoSuchElementException:
                fabric_care_text = ""

            # Rating & reviews
            rating_text = self.get_text_or_empty('//div[contains(@class,"yotpo-bottom-line-score")]')
            reviews_text = self.get_text_or_empty('//span[contains(@class,"yotpo-sr-bottom-line-text")]').replace("Reviews", "").strip()

            # Images
            image_elements = self.driver.find_elements(By.XPATH, '//div[contains(@class,"Product__SlideshowNavScroller")]//img')
            image_urls = [img.get_attribute("src") for img in image_elements if img.get_attribute("src")]

            return {
                "brand": brand_text,
                "product_title": name_text,
                "color": color_text,
                "price": price_text,
                "sizes": size_list,
                "description": editor_notes,
                "size_and_fit": size_fit,
                "fabric_and_care": fabric_care_text,
                "rating": rating_text,
                "reviews": reviews_text,
                "images": image_urls,
                "url": url
            }

        except Exception as e:
            self.logger.error(f"Error parsing product page {url}: {e}")
            return None

    def scrape_products(self):
        """Main scraping method for all product URLs"""
        self.connect_mongo()
        self.setup_driver(headless=True)
        self.start_time = time.time()
        product_urls = self.fetch_product_urls()

        if not product_urls:
            self.logger.warning("No product URLs found to scrape.")
            return

        for url in product_urls:
            try:
                self.logger.info(f"Scraping product: {url}")
                product_data = self.parse_product_page(url)
                if product_data:
                    self.save_product_data(product_data)
            except TimeoutException as e:
                self.logger.error(f"Timeout scraping URL {url}: {e}")
            except Exception as e:
                self.logger.error(f"Error scraping URL {url}: {e}")

        self.driver.quit()
        self.print_efficiency()

    def print_efficiency(self):
        """Print memory and CPU usage efficiency"""
        elapsed_time = time.time() - self.start_time
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()

        self.logger.info("===== PRODUCT SCRAPING EFFICIENCY =====")
        self.logger.info(f"Total time elapsed: {elapsed_time:.2f} seconds")
        self.logger.info(f"CPU usage: {cpu_percent}%")
        self.logger.info(f"Memory usage: {memory_info.percent}%")
        self.logger.info("=======================================")

    def close(self):
        if self.client:
            self.client.close()
            self.logger.info("MongoDB connection closed.")


if __name__ == "__main__":
    parser = Carbon38ProductParserSelenium()
    parser.scrape_products()
    parser.close()
