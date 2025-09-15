import logging
import psutil
import time
import re
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from curl_cffi import requests
from lxml import html


class Carbon38ProductParser:
    def __init__(self, mongo_uri="mongodb://localhost:27017/", db_name="carbon38",
                 url_collection="curlcffi_url", product_collection="curlcffi_data"):
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

        # Yotpo store ID (static for Carbon38)
        self.store_id = "77OFfab03RDNwJXqpx5Bl5qmZJcAjybjX3EnuxBh"
        
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
    
    # ------------------------------
    # RATING + REVIEW EXTRACTION
    # ------------------------------
    def extract_rating_from_script(self, html_text):
        """
        Extracts Yotpo rating from <script id="viewed_product">.
        Returns rating as a string. Returns '0' if not found.
        """
        script_match = re.search(r'<script id="viewed_product"[^>]*>(.*?)</script>', html_text, re.S)
        script_text = script_match.group(1) if script_match else ""
        rating_match = re.search(r'MetafieldYotpoRating\s*=\s*"([0-9.]+)"', script_text)
        return rating_match.group(1).strip() if rating_match else "0"

    def extract_product_id(self, html_text):
        """
        Extracts Yotpo product ID from the HTML.
        """
        product_id_match = re.search(r'data-yotpo-product-id="(\d+)"', html_text)
        return product_id_match.group(1) if product_id_match else None

    def fetch_reviews(self, product_id):
        """
        Calls the Yotpo API using curl_cffi and returns review count.
        """
        api_url = (
            f"https://api-cdn.yotpo.com/v3/storefront/store/{self.store_id}"
            f"/product/{product_id}/reviews?page=1&perPage=1"
        )
        try:
            resp = requests.get(api_url, impersonate="chrome")
            resp.raise_for_status()
            data = resp.json()
            return str(data.get("pagination", {}).get("total", 0))
        except Exception as e:
            logging.warning(f"Failed to fetch reviews for product {product_id}: {e}")
            return "0"
    
    def parse_product_page(self, page_html, url):
        """Extract detailed product information from HTML using XPath"""
        try:
            tree = html.fromstring(page_html)

            brand = tree.xpath('//h2[contains(@class,"ProductMeta__Vendor Heading u-h1")]/a/text()')
            brand_text = brand[0].strip() if brand else ""

            name = tree.xpath('//h1[contains(@class,"ProductMeta__Title Heading u-h3")]/text()')
            name_text = name[0].strip() if name else ""

            color = tree.xpath('//span[contains(@class,"ProductForm__SelectedValue ")]/text()')
            color_text = color[0].strip() if color else ""

            price = tree.xpath('//span[contains(@class,"ProductMeta__Price Price")]/text()')
            price_text = price[0].replace("$","").replace("USD","").strip() if price else ""

            sizes = tree.xpath('//input[contains(@class,"SizeSwatch__Radio")]/@value')
            size_list = [s for s in sizes if s]

            faq_elements = tree.xpath('.//div[contains(@class,"Faq__AnswerWrapper")]//p')
            editor_notes = faq_elements[0].text_content().strip() if len(faq_elements) > 0 else ""
            size_fit = faq_elements[1].text_content().strip() if len(faq_elements) > 1 else ""

            fabric_care_el = tree.xpath('.//div[contains(@class,"Faq__AnswerWrapper")]//p/span')
            if fabric_care_el:
                raw_html = html.tostring(fabric_care_el[0], encoding="unicode", method="html")
                fabric_care_text = re.sub(r'<br\s*/?>', '\n', raw_html)
                fabric_care_text = re.sub(r'<[^>]+>', '', fabric_care_text).strip()
            else:
                fabric_care_text = ""

            images = tree.xpath('//div[contains(@class,"Product__SlideshowNavScroller")]//img/@src')
            image_urls = [img for img in images if img]

            return {
                "brand": brand_text,
                "product_title": name_text,
                "color": color_text,
                "price": price_text,
                "sizes": size_list,
                "description": editor_notes,
                "size_and_fit": size_fit,
                "fabric_and_care": fabric_care_text,
                "rating": self.extract_rating_from_script(page_html),
                "reviews": self.fetch_reviews(self.extract_product_id(page_html)),
                "images": image_urls,
                "url": url
            }

        except Exception as e:
            self.logger.error(f"Error parsing product page {url}: {e}")
            return None

    def scrape_products(self):
        """Scrape all product URLs using curl_cffi"""
        self.connect_mongo()
        self.start_time = time.time()
        product_urls = self.fetch_product_urls()

        if not product_urls:
            self.logger.warning("No product URLs found to scrape.")
            return

        for url in product_urls:
            try:
                self.logger.info(f"Scraping product: {url}")
                resp = requests.get(url, impersonate="chrome", timeout=60)
                resp.raise_for_status()
                product_data = self.parse_product_page(resp.text, url)
                if product_data:
                    self.save_product_data(product_data)
            except Exception as e:
                self.logger.error(f"Error scraping URL {url}: {e}")

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
