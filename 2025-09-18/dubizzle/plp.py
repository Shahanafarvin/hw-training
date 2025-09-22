
"""
Playwright scraper with stealth and MongoDB category+subcategory+products nesting.
"""

import time
import random
import logging
from urllib.parse import urljoin
from pymongo import MongoClient, UpdateOne
from pymongo.errors import PyMongoError
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Config
BASE_URL = "https://www.dubizzle.com.bh/"
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "dubizzle_db"
PLAYWRIGHT_NAV_TIMEOUT = 60_000  # ms
CHALLENGE_WAIT = 10

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

def random_ua():
    uas = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    ]
    return random.choice(uas)


class DubizzlePlaywrightStealthScraper:
    def __init__(self, base_url=BASE_URL, mongo_uri=MONGO_URI, db_name=DB_NAME):
        self.base_url = base_url
        self.mongo = MongoClient(mongo_uri)
        self.db = self.mongo[db_name]
        self.categories_col = self.db.categories

    # ---------- Mongo Save ----------
    def _upsert_category(self, cat_name, sub_url, products):
        """Upsert category with subcategory and its products into MongoDB"""
        try:
            # Ensure category doc exists and has subcategories as array
            self.categories_col.update_one(
                {"name": cat_name},
                {"$setOnInsert": {"subcategories": []}},
                upsert=True
            )

            # Try updating products inside existing subcategory
            result = self.categories_col.update_one(
                {"name": cat_name, "subcategories.url": sub_url},
                {"$addToSet": {"subcategories.$.products": {"$each": products}}}
            )

            # If no subcategory matched, push a new subcategory object
            if result.matched_count == 0:
                self.categories_col.update_one(
                    {"name": cat_name},
                    {"$push": {"subcategories": {"url": sub_url, "products": products}}}
                )

            logging.info(f"📥 Updated category '{cat_name}' with {len(products)} products in {sub_url}")

        except PyMongoError as e:
            logging.error(f"Mongo error: {e}")


    # ---------- Extraction ----------
    def _extract_categories(self, page):
        logging.info(" Extracting categories...")
        cats = []

        nodes = page.query_selector_all(
            'xpath=//div[contains(@class,"_948d9e0a _66b37327 _95d4067f")]'
        )

        for node in nodes:
            title_el = node.query_selector(
                'xpath=.//span[contains(@class,"a1c1940e b7af14b4")]'
            )
            cat_name = title_el.inner_text().strip() if title_el else "Unknown"

            subs = []
            for a in node.query_selector_all("a"):
                href = a.get_attribute("href")
                if href:
                    subs.append(urljoin(self.base_url, href))

            cats.append({"name": cat_name, "subcategories": subs})

        logging.info(f" Extracted {len(cats)} categories")
        return cats

    def _extract_products(self, page):
        logging.info(" Extracting product links...")
        products = set()

        links1 = page.query_selector_all('xpath=//div[@class="b5af0448"]/a')
        links2 = page.query_selector_all('xpath=//div[contains(@class,"_70cdfb32")]/a')
        links3 = page.query_selector_all('xpath=//div[@class="d6ce1d5a"]//a')

        for link in links1 + links2 + links3:
            href = link.get_attribute("href")
            if href:
                products.add(urljoin(self.base_url, href))

        logging.info(f" Extracted {len(products)} products")
        return list(products)
    
    def _extract_products_with_pagination(self, page, cat_name, sub_url):
        """Extract all products from paginated subcategory using click navigation"""
        all_products = set()

        while True:
            
            #  Extract products from current page
            products = self._extract_products(page)
            all_products.update(products)

            #  Find the "Next" button
            next_btn = page.query_selector("//div[@role='navigation']//ul/li[last()]/a")
            #print(next_btn.inner_html())
            if not next_btn or "disabled" in (next_btn.get_attribute("class") or ""):
                break  # no more pages

            try:
                logging.info(" Clicking next page...")
                next_btn.click()
                page.wait_for_load_state("domcontentloaded", timeout=PLAYWRIGHT_NAV_TIMEOUT)
                time.sleep(random.uniform(2, 5))  # human-like pause
            except PWTimeout:
                logging.warning(f" Timeout while clicking next page in {sub_url}")
                break

        logging.info(f" {len(all_products)} total products for {sub_url}")
        if all_products:
            self._upsert_category(cat_name, sub_url, list(all_products))


    # ---------- Runner ----------
    def run(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(user_agent=random_ua())
            page = context.new_page()
            page.add_init_script(STEALTH_INIT_JS)

            logging.info(" Navigating to homepage...")
            try:
                page.goto(self.base_url, timeout=PLAYWRIGHT_NAV_TIMEOUT)
                time.sleep(CHALLENGE_WAIT)
            except PWTimeout:
                logging.error(" Timeout loading homepage")
                return

            categories = self._extract_categories(page)

            for cat in categories:
                for sub_url in cat["subcategories"][:2]:   #  first two only
                    try:
                        page.goto(sub_url,timeout=PLAYWRIGHT_NAV_TIMEOUT)
                        time.sleep(random.uniform(3, 6))
                        self._extract_products_with_pagination(page, cat["name"], sub_url)
                    except PWTimeout:
                        logging.warning(f"Timeout on {sub_url}")


            browser.close()


if __name__ == "__main__":
    scraper = DubizzlePlaywrightStealthScraper()
    scraper.run()
