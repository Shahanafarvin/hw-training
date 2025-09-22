
"""
Playwright product parser for Dubizzle, extracting full product details
and saving into a dedicated MongoDB collection.
"""

import time
import random
import logging
from datetime import datetime
from urllib.parse import urljoin
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Config
BASE_URL = "https://www.dubizzle.com.bh/"
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "dubizzle_db"
PLAYWRIGHT_NAV_TIMEOUT = 60_000
CHALLENGE_WAIT = 5
UA_FILE = "/home/shahana/datahut-training/hw-training/user_agents.txt"

STEALTH_INIT_JS = r"""
Object.defineProperty(navigator, 'webdriver', { get: () => false });
Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
const origQuery = window.navigator.permissions && window.navigator.permissions.query;
if (origQuery) {
  window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications'
      ? Promise.resolve({ state: Notification.permission })
      : origQuery(parameters)
  );
}
if (window.chrome === undefined) { window.chrome = { runtime: {} }; }
"""

# -------- User Agent Loader --------
def load_user_agents(path=UA_FILE):
    try:
        with open(path, "r") as f:
            uas = [ua.strip() for ua in f if ua.strip()]
        if not uas:
            raise ValueError("User agent file is empty")
        return uas
    except Exception as e:
        logging.error(f"Failed to load user agents from {path}: {e}")
        return ["Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"]

USER_AGENTS = load_user_agents()

def random_ua():
    return random.choice(USER_AGENTS)


class DubizzleProductParser:
    def __init__(self, base_url=BASE_URL, mongo_uri=MONGO_URI, db_name=DB_NAME):
        self.base_url = base_url
        self.mongo = MongoClient(mongo_uri)
        self.db = self.mongo[db_name]
        self.categories_col = self.db.categories
        self.products_col = self.db.products

    # ---------- Mongo Save ----------
    def _save_product(self, data):
        try:
            self.products_col.update_one(
                {"reference_number": data.get("reference_number")},
                {"$set": data},
                upsert=True
            )
            logging.info(f" Saved product {data.get('reference_number')} - {data.get('title')}")
        except PyMongoError as e:
            logging.error(f"Mongo error: {e}")

    def _extract_highlighted_details(self, page):
        """Extract highlighted details as list of key-value JSON objects"""
        details = []
        rows = page.query_selector_all('//div[@aria-label="Highlighted Details"]/div')
        for row in rows:
            spans = row.query_selector_all("span")
            if len(spans) >= 2:
                key = spans[0].inner_text().strip()
                value = spans[1].inner_text().strip()
                if key and value:
                    details.append({key: value})
        return details

    # ---------- Extraction ----------
    def _extract_product_details(self, page, url, category, category_url):
        """Extract required fields from product page"""
        def safe_text(selector, attr=""):
            el = page.query_selector(selector)
            #print(el)
            if not el:
                return ""
            return el.inner_text().strip() if not attr else el.get_attribute(attr)
        

        product = {
            "reference_number": safe_text('xpath=//div[@class="_114d5a00"]').replace("رقم الإعلان", "").strip(),
            "url": url,
            "broker_display_name": safe_text('xpath=//div[@class="_948d9e0a _371e9918"]/span'),
            "category": category,
            "category_url": category_url,
            "title": safe_text('xpath=//h1[@class="_75bce902"]'),
            "description": safe_text('xpath=//div[@class="_472bfbef"]//span'),
            "location": safe_text('xpath=//span[@aria-label="Location"]'),
            "price": safe_text('xpath=//span[@aria-label="Price"]').replace("BHD", "").replace(",", "").strip(),
            "currency": 'BHD',
            "highlight": self._extract_highlighted_details(page),
            "scraped_ts":datetime.utcnow().strftime("%Y-%m-%d")
        }
        return product

    # ---------- Runner ----------
    def run(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)

            cats = self.categories_col.find()
            for cat in cats:
                cat_name = cat["name"]
                for sub in cat.get("subcategories", []):
                    sub_url = sub["url"]
                    for product_url in sub.get("products", []):
                        # rotate UA for each request
                        context = browser.new_context(user_agent=random_ua())
                        page = context.new_page()
                        page.add_init_script(STEALTH_INIT_JS)

                        try:
                            logging.info(f" Visiting {product_url}")
                            page.goto(product_url, timeout=PLAYWRIGHT_NAV_TIMEOUT)
                            time.sleep(random.uniform(3, 6))
                            data = self._extract_product_details(page, product_url, cat_name, sub_url)
                            if data:
                                self._save_product(data)
                        except PWTimeout:
                            logging.warning(f" Timeout while visiting {product_url}")
                        finally:
                            context.close()

            browser.close()


if __name__ == "__main__":
    parser = DubizzleProductParser()
    parser.run()
