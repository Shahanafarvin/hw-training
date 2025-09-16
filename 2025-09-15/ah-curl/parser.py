import logging
import time
import random
from lxml import html
from curl_cffi import requests as curl_requests
from pymongo import MongoClient
from pymongo.errors import PyMongoError

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

BASE_URL = "https://www.ah.nl"

class AHProductScraper:
    """
    A scraper for extracting product details from the Albert Heijn (ah.nl) website.

    This scraper uses:
      - `curl_cffi` to mimic browser-like requests and handle sessions.
      - `lxml` for parsing HTML responses.
      - `MongoDB` to store scraped categories (input) and product details (output).

    Workflow:
      1. Reads product URLs from the `categories` collection in MongoDB.
      2. Fetches each product page.
      3. Extracts product details such as title, price, brand, description, etc.
      4. Saves structured product data into the `products` collection in MongoDB.

    Attributes:
        session (curl_requests.Session): A persistent session for reusing cookies and headers.
        client (MongoClient): MongoDB client for database interaction.
        db (Database): The active MongoDB database.
        products_col (Collection): Collection where product data will be stored.
        categories_col (Collection): Collection that stores categories with their product URLs.
        default_headers (dict): Default HTTP headers for all requests.
    """
    def __init__(self, mongo_uri="mongodb://localhost:27017/", db_name="ah_scraper"):
        """
        Initialize the scraper with MongoDB connection and default HTTP headers.

        Args:
            mongo_uri (str, optional): URI string to connect to MongoDB.
                Defaults to "mongodb://localhost:27017/".
            db_name (str, optional): Name of the MongoDB database to use.
                Defaults to "ah_scraper".
        """
        self.session = curl_requests.Session()
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.products_col = self.db["products"]        # collection to save product data
        self.categories_col = self.db["categories"]    # collection with saved URLs

        self.default_headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/137.0.0.0 Safari/537.36",
            "referer": BASE_URL,
        }

    def fetch_page(self, url):
        """
        Fetch an HTML page with retries and a random delay.

        Args:
            url (str): The URL of the product page to fetch.

        Returns:
            str | None: The HTML content of the page, or None if the request fails.
        """
        try:
            delay = random.uniform(1, 4)
            logging.info(f"Sleeping {delay:.2f}s before fetching {url}")
            time.sleep(delay)

            resp = self.session.get(
                url,
                impersonate="chrome123",
                headers=self.default_headers,
                timeout=60
            )
            if resp.status_code != 200:
                logging.error(f"Failed to fetch {url} (status: {resp.status_code})")
                return None
            return resp.text
        except Exception as e:
            logging.error(f"Error fetching {url}: {e}")
            return None

    def parse_product_page(self, html_content):
        """
        Parse a product detail page and extract structured data.

        Args:
            html_content (str): Raw HTML content of a product page.

        Returns:
            dict: A dictionary with extracted product fields, which may include:
                - title (str | None): Product title.
                - breadcrumbs (list[str]): List of breadcrumb category names.
                - brand (str | None): Product brand name.
                - price (str | None): Product price (in euros).
                - unit_wt (str | None): Unit weight or size info.
                - nutriscore (str | None): Nutri-Score label if available.
                - description (str): Product description text.
                - ingredients (list[str]): List of ingredient texts.
                - storage_instructions (str | None): Storage instructions if available.
        """
        tree = html.fromstring(html_content)
        data = {}

        try:
            # Example XPaths — adjust according to actual HTML structure
            data['title'] = tree.xpath('//span[contains(@class,"line-clamp_root__7DevG line-clamp_active__5Qc2L")]/text()')
            data['title'] = data['title'][0].strip() if data['title'] else None

            data['breadcrumbs'] = tree.xpath('//span[@class="breadcrumbs_text__f36Jd"]/text()')
            data['breadcrumbs'] = [b.strip() for b in data['breadcrumbs'] if b.strip()]

            data['brand'] = tree.xpath('//a[contains(@class,"button-or-anchor_root__LgpRR button-bare_root__w0spa brand-button")]/text()')
            data['brand'] = data['brand'][0].strip() if data['brand'] else None

            price_el = tree.xpath('//span[contains(@class,"sr-only")]')
            data['price'] = price_el[0].get("aria-label").replace("Prijs: €","").strip() if price_el else None


            data['unit_wt'] = tree.xpath('//span[contains(@class,"product-card-hero-price_unitSize__ReamD")]/text()')
            data['unit_wt'] = data['unit_wt'][0].strip() if data['unit_wt'] else None

            # Nutriscore, if exists
            data['nutriscore'] = tree.xpath('//div[contains(@data-testhook,"pdp-hero-nutriscore")]//svg//text()')
            data['nutriscore'] = data['nutriscore'][0].replace("Nutri-Score","").strip() if data['nutriscore'] else None

            # Description
            data['description'] = tree.xpath('//div[contains(@data-testhook,"product-summary")]//text()')
            data['description'] = " ".join([d.strip() for d in data['description'] if d.strip()])

            ingredients = tree.xpath('//div[contains(@data-testhook,"pdp-info-content")]//text()')
            data['ingredients'] = [ing.strip() for ing in ingredients if ing.strip()]  

            save=tree.xpath('//div[contains(@class,"accordion_content__qzOgU")]//text()')
            data['storage_instructions'] = save[0].strip() if save else None

            # You can add more fields as needed (e.g., images, GTINs, categories)
        except Exception as e:
            logging.error(f"Error parsing HTML: {e}")

        return data

    def run(self):
        """
        Execute the scraping process across all saved categories and products.

        Workflow:
            1. Load categories from `categories` collection.
            2. Iterate over each product URL in each category.
            3. Fetch product page HTML.
            4. Parse product details using XPath.
            5. Save product data into the `products` collection in MongoDB.

        Returns:
            None
        """
        all_categories = self.categories_col.find({})
        for cat in all_categories:
            product_urls = cat.get("products", [])
            logging.info(f"Processing category: {cat['name']} ({len(product_urls)} products)")
            for url in product_urls:
                html_content = self.fetch_page(url)
                if not html_content:
                    continue

                product_data = self.parse_product_page(html_content)
                product_data['url'] = url
                product_data['category'] = cat['name']

                try:
                    self.products_col.insert_one(product_data)
                    logging.info(f"Saved product: {product_data.get('title')}")
                except PyMongoError as e:
                    logging.error(f"MongoDB insert error for {url}: {e}")

if __name__ == "__main__":
    scraper = AHProductScraper()
    scraper.run()
