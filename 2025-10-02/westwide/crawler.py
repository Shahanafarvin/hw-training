
import logging
import time
from urllib.parse import urljoin

from lxml import html
from pymongo import MongoClient, errors
from playwright.sync_api import sync_playwright


MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "westside"
CATEGORIES_COLLECTION = "categories"
START_URL = "https://www.westside.com/"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("westside")


class WestsideScraper:
    def __init__(self, mongo_uri=MONGO_URI, headless=True):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[MONGO_DB]
        self.cat_col = self.db[CATEGORIES_COLLECTION]
        self.cat_col.create_index("url", unique=True)
        self.headless = headless

    def __enter__(self):
        self._p = sync_playwright().start()
        self.browser = self._p.chromium.launch(headless=self.headless)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.browser.close()
        self._p.stop()
        self.client.close()

    def _infinite_scroll(self, page, item_xpath="//a[contains(@class,'wizzy-result-product-item')]", pause=1.5, max_rounds=50):
        """
        Scrolls in chunks and extracts product URLs dynamically.
        Returns a list of product hrefs.
        """
        seen_hrefs = set()
        prev_count = 0

        for _ in range(max_rounds):
            page.evaluate("window.scrollBy(0, window.innerHeight);")
            time.sleep(pause)
            tree = html.fromstring(page.content())
            new_hrefs = set(tree.xpath(item_xpath))
            seen_hrefs.update(new_hrefs)

            # Stop if no new products appear after scroll
            if len(seen_hrefs) == prev_count:
                break
            prev_count = len(seen_hrefs)

        return list(seen_hrefs)

    def get_category_urls(self):
        """
        Extract Men’s category URLs with a SINGLE XPath.
        """
        page = self.browser.new_page()
        page.goto(START_URL, wait_until="domcontentloaded")

        tree = html.fromstring(page.content())
      
        category_el = tree.xpath("//ul[@class='last-child western-wear']")
        category_hrefs = category_el[4].xpath(".//a/@href") if category_el else []

        categories = []
        for href in category_hrefs:
            abs_url = urljoin(START_URL, href)
            try:
                self.cat_col.insert_one({"url": abs_url, "scraped": False, "products": []})
                logger.info(f"Saved category: {abs_url}")
            except errors.DuplicateKeyError:
                pass
            categories.append(abs_url)

        page.close()
        return categories

    def extract_products_from_category(self, category_url: str):
        """
        Extract product URLs from a category page with a SINGLE XPath.
        Save them into the same category doc as a list.
        """
        page = self.browser.new_page()
        page.goto(category_url, wait_until="domcontentloaded")

        self._infinite_scroll(page)

        tree = html.fromstring(page.content())
        product_hrefs = tree.xpath("//a[@class='wizzy-result-product-item']/@href")

        product_urls = [urljoin(category_url, href) for href in set(product_hrefs)]

        # update category document with product list
        self.cat_col.update_one(
            {"url": category_url},
            {"$set": {"scraped": True, "products": product_urls}},
            upsert=True
        )

        logger.info(f"Saved {len(product_urls)} products for category: {category_url}")
        page.close()

    def crawl(self):
        categories = self.get_category_urls()
        for cat_url in categories:
            cat_doc = self.cat_col.find_one({"url": cat_url})
            if not cat_doc or not cat_doc.get("scraped"):
                self.extract_products_from_category(cat_url)


if __name__ == "__main__":
    with WestsideScraper(headless=False) as scraper:
        scraper.crawl()
