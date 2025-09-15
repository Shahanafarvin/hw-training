import logging
import psutil
import time
import re
from playwright.sync_api import sync_playwright
from pymongo import MongoClient
from pymongo.errors import PyMongoError


class Carbon38ProductParser:
    def __init__(self, mongo_uri="mongodb://localhost:27017/", db_name="carbon38",
                 url_collection="playwright_urls", product_collection="playwright_data"):
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.url_collection_name = url_collection
        self.product_collection_name = product_collection
        self.client = None
        self.db = None
        self.url_collection = None
        self.product_collection = None
        self.start_time = None

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

    def parse_product_page(self, page):
        """Extract detailed product information from a page"""
        try:
            brand=page.query_selector('xpath=//h2[contains(@class,"ProductMeta__Vendor Heading u-h1")]/a')
            brand_text = brand.inner_text().strip() if brand else ""

            name = page.query_selector('xpath=//h1[contains(@class,"ProductMeta__Title Heading u-h3")]')
            name_text = name.inner_text().strip() if name else ""

            color=page.query_selector('xpath=//span[contains(@class,"ProductForm__SelectedValue ")]')
            color_text = color.inner_text().strip() if color else ""

            price = page.query_selector('xpath=//span[contains(@class,"ProductMeta__Price Price")]')
            price_text = price.inner_text().replace("$","").replace("USD","").strip() if price else ""

            sizes = page.query_selector_all('xpath=//input[contains(@class,"SizeSwatch__Radio")]')
            size_list = [size.get_attribute("value") for size in sizes if size.get_attribute("value")]  

            faq_element = page.query_selector_all('xpath=.//div[contains(@class,"Faq__AnswerWrapper")]//p')
            editor_notes = faq_element[0].inner_html() if faq_element else ""
            size_fit = faq_element[1].inner_html() if len(faq_element) > 1 else ""
            fabric_care = page.query_selector('xpath=.//div[contains(@class,"Faq__AnswerWrapper")]//p/span')
            if fabric_care:
                raw_html = fabric_care.inner_html()
                # Replace <br> with newline
                fabric_care_text = re.sub(r'<br\s*/?>', '\n', raw_html)
                # Remove any other HTML tags
                fabric_care_text = re.sub(r'<[^>]+>', '', fabric_care_text).strip()             

        
            rating=page.query_selector('xpath=//div[contains(@class,"yotpo-bottom-line-left-panel yotpo-bottom-line-score")]')
            rating_text = rating.inner_text().strip() if rating else ""

            reviews=page.query_selector('xpath=//span[contains(@class,"yotpo-sr-bottom-line-text yotpo-sr-bottom-line-text--right-panel")]')
            reviews_text = reviews.inner_text().replace("Reviews","").strip() if reviews else ""

            images = page.query_selector_all('xpath=//div[contains(@class,"Product__SlideshowNavScroller")]//img')
            image_urls = [img.get_attribute("src") for img in images if img.get_attribute("src")]

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
                "url": page.url
            }
        except Exception as e:
            self.logger.error(f"Error parsing product page {page.url}: {e}")
            return None

    def scrape_products(self):
        """Main scraping method for all product URLs"""
        self.connect_mongo()
        self.start_time = time.time()
        product_urls = self.fetch_product_urls()

        if not product_urls:
            self.logger.warning("No product URLs found to scrape.")
            return

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            for url in product_urls:
                try:
                    page.goto(url,  timeout=120000, wait_until="domcontentloaded")
                    #time.sleep(7)
                    self.logger.info(f"Scraping product: {url}")
                    product_data = self.parse_product_page(page)
                    if product_data:
                        self.save_product_data(product_data)
                except Exception as e:
                    self.logger.error(f"Error scraping URL {url}: {e}")

            browser.close()
    
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
    parser = Carbon38ProductParser()
    parser.scrape_products()
    parser.close()
