
import logging
import time
from urllib.parse import urljoin

from lxml import html
from pymongo import MongoClient, errors
from playwright.sync_api import sync_playwright

MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "westside"
CATEGORIES_COLLECTION = "categories"
PRODUCTS_COLLECTION = "products"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("westside_product_scraper")


class WestsideProductScraper:
    def __init__(self, mongo_uri=MONGO_URI, headless=True):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[MONGO_DB]
        self.cat_col = self.db[CATEGORIES_COLLECTION]
        self.prod_col = self.db[PRODUCTS_COLLECTION]
        self.prod_col.create_index("url", unique=True)
        self.headless = headless

    def __enter__(self):
        self._p = sync_playwright().start()
        self.browser = self._p.chromium.launch(headless=self.headless)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.browser.close()
        self._p.stop()
        self.client.close()

    def _extract_product_data(self, page):
        """
        Extract product details using XPaths.
        """
        tree = html.fromstring(page.content())

        data = {}
        try:
            breadcrumbs = tree.xpath("//li[@class='breadcrumbs__item']//text()")
            data['breadcrumbs'] = [b.strip() for b in breadcrumbs if b.strip()]
            brand_el = tree.xpath("//p[@class='product__text inline-richtext caption-with-letter-spacing']/text()")
            data['brand'] = brand_el[0].strip() if brand_el else None
            title_el = tree.xpath("//div[@class='product__title']/h1/text()")
            data['title'] = title_el[0].strip() if title_el else None
            price_el = tree.xpath("//span[@class='price-item price-item--regular']/text()")
            data['price'] = price_el[0].replace("₹","").strip() if price_el else None
            
            # Extract <div class="features">
            features_divs = tree.xpath('//div[@class="features"]')

            for div in features_divs:
                key = div.xpath('.//b/text()')
                key = key[0].strip(':').lower().replace(" ","_") if key else None
                value = div.xpath('text()')
                value = ''.join([v.strip() for v in value if v.strip()])  # remove extra whitespace
                if key and value:
                    data[key] = value

    
            # Extract <div class="features_discription">
            desc_divs = tree.xpath('//div[contains(@class,"features_discription")]//text()')
            description = ' '.join([d.strip() for d in desc_divs if d.strip()])
            if description:
                data['Description'] = description

        except Exception as e:
            logger.warning(f"Error extracting breadcrumbs: {e}")
           

        return data

    def scrape_product(self, product_url):
        page = self.browser.new_page()
        try:
            page.goto(product_url, wait_until="domcontentloaded")
            time.sleep(2)  # wait for dynamic content to load
            data = self._extract_product_data(page)
            data['url'] = product_url

            try:
                self.prod_col.insert_one(data)
                logger.info(f"Saved product: {product_url}")
            except errors.DuplicateKeyError:
                logger.info(f"Duplicate product skipped: {product_url}")

        except Exception as e:
            logger.error(f"Error scraping {product_url}: {e}")
        finally:
            page.close()

    def crawl_all_products(self):
        """
        Go through all saved category URLs and scrape each product.
        """
        for cat_doc in self.cat_col.find({"scraped": True}):
            product_urls = cat_doc.get("products", [])
            for url in product_urls:
                if not self.prod_col.find_one({"url": url}):
                    self.scrape_product(url)
                    time.sleep(1)  # optional delay to avoid rate limiting


if __name__ == "__main__":
    with WestsideProductScraper(headless=False) as scraper:
        scraper.crawl_all_products()
