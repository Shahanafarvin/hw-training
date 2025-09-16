import logging
import random
import time
import os
from curl_cffi import requests as curl_requests
from pymongo import MongoClient
from pymongo.errors import PyMongoError

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

BASE_URL = "https://www.ah.nl"


class AHScraper:
    """
    A scraper for extracting product category and product data from the Albert Heijn (ah.nl) website.

    This class leverages `curl_cffi` for making HTTP requests with browser impersonation,
    and MongoDB for storing category and product data. Categories are scraped from the homepage,
    and products are extracted via AH's JSON API endpoints.

    Attributes:
        session (curl_requests.Session): Persistent session object for managing cookies and headers.
        client (MongoClient): MongoDB client for database connection.
        db (Database): MongoDB database instance.
        categories_col (Collection): MongoDB collection for storing category data.
        default_headers (dict): HTTP headers used for requests.
    """
    def __init__(self, mongo_uri="mongodb://localhost:27017/", db_name="ah_scraper"):
        """
        Initialize the AHScraper instance.

        Args:
            mongo_uri (str): MongoDB connection URI. Defaults to "mongodb://localhost:27017/".
            db_name (str): MongoDB database name. Defaults to "ah_scraper".
        """
        # Use a persistent session
        self.session = curl_requests.Session()
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.categories_col = self.db["categories"]

        self.default_headers = {
            "accept": "application/json",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/137.0.0.0 Safari/537.36",
            "referer": "https://www.ah.nl/",
        }

    def fetch_page(self, url):
        """
        Fetch an HTML page while reusing cookies and headers.

        Args:
            url (str): The target URL to fetch.

        Returns:
            str | None: The HTML response text if successful, otherwise None.
        """
        try:
            delay = random.uniform(1, 5)
            logging.info(f"Sleeping for {delay:.2f} seconds before fetching {url}")
            time.sleep(delay)

            response = self.session.get(
                url,
                impersonate="chrome123",
                headers=self.default_headers,
                timeout=60
            )

            logging.info(f"Fetched {url} (status: {response.status_code})")
            if response.status_code != 200:
                logging.error(f"Failed fetching {url} (status: {response.status_code})")
                return None

            return response.text

        except Exception as e:
            logging.error(f"Request failed for {url}: {e}")
            return None


    def fetch_api(self, url):
        """
        Fetch a JSON API response from AH's product API.

        Args:
            url (str): API endpoint URL.

        Returns:
            dict | None: Parsed JSON response if successful, otherwise None.
        """
        try:
            #delay = random.uniform(1, 3)
            #logging.info(f"Sleeping {delay:.2f}s before {url}")
            #time.sleep(delay)

            resp = self.session.get(
                url,
                impersonate="chrome123",
                headers=self.default_headers,
                timeout=60
            )

            if resp.status_code != 200:
                logging.error(f"API call failed ({resp.status_code}) {url}")
                return None
            return resp.json()
        except Exception as e:
            logging.error(f"API request failed: {e}")
            return None

    def scrape_categories(self, url=BASE_URL):
        """
        Scrape product categories from the AH homepage.

        Categories are identified via HTML anchor tags with `data-testhook="super-shop-card"`.
        Each category includes name, URL, slug, and placeholder for taxonomy and product list.

        Args:
            url (str): Homepage URL. Defaults to BASE_URL.

        Returns:
            list[dict]: A list of category dictionaries with keys:
                - name (str): Category name.
                - url (str): Full category URL.
                - slug (str): Extracted slug from category URL.
                - taxonomy (str | None): Placeholder for taxonomy.
                - products (list): Initially empty product list.
        """
        # For now, keeping the HTML-based scraping
        from lxml import html

        logging.info("Scraping categories...")
        html_content = self.fetch_page(url)

        if not html_content:
            return []

        tree = html.fromstring(html_content)
        category_elements = tree.xpath('//a[@data-testhook="super-shop-card"]')

        categories = []
        for a in category_elements:
            href = a.get("href")
            text = a.xpath('string(.//p)')
            if href and text.strip():
                categories.append({
                    "name": text.strip(),
                    "url": BASE_URL + href,
                    "slug": href.split("/")[-1],  # Extract slug from URL
                    "taxonomy": None,  # Can be filled manually or dynamically later
                    "products": []
                })
        return categories

    def extract_products_from_api(self, data):
        """
        Extract product URLs from API JSON data.

        Args:
            data (dict): Parsed API response JSON.

        Returns:
            list[str]: List of product page URLs.
        """
        products = []
        for card in data.get("cards", []):
            for product in card.get("products", []):
                link = product.get("link")
                if link:
                    products.append(BASE_URL + link)
        return products

    def scrape_products_from_category(self, category):
        """
        Scrape all product URLs for a given category via the AH product API.

        Args:
            category (dict): Category dictionary with `url` key.

        Returns:
            list[str]: All product URLs found in the category.
        """
        products = []

        # Extract taxonomy from category URL
        taxonomy_id = category['url'].split("/producten/")[1].split("/")[0]
        page = 1
        size = 36

        while True:
            api_url = (f"{BASE_URL}/zoeken/api/products/search?"
                    f"page={page}&size={size}&taxonomy={taxonomy_id}")
            data = self.fetch_api(api_url)
            if not data or "page" not in data:
                break

            # Extract products
            page_products = self.extract_products_from_api(data)
            if not page_products:
                break

            products += page_products
            logging.info(f"Page {page}/{data['page']['totalPages']}: Scraped {len(page_products)} products")
        
            if page >= data['page']['totalPages']:
                break

            page += 1

        return products

    def run(self):
        """
        Run the scraping process.

        Steps:
        1. Scrape categories from homepage.
        2. Skip the first and last categories.
        3. Scrape product URLs for each category via API.
        4. Save results into MongoDB.

        Returns:
            None
        """
        categories = self.scrape_categories()
        if not categories:
            logging.warning("No categories found.")
            return

        # Skip first and last category
        categories_to_process = categories[1:-1]

        self.categories_col.delete_many({})
        for category in categories_to_process:
            category["products"] = self.scrape_products_from_category(category)
            try:
                self.categories_col.insert_one(category)
                logging.info(f"Saved category {category['name']} with {len(category['products'])} products")
            except PyMongoError as e:
                logging.error(f"MongoDB insert error: {e}")

if __name__ == "__main__":
    scraper = AHScraper()
    scraper.run()
