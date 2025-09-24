#!/usr/bin/env python3
import requests
from lxml import html
from pymongo import MongoClient
import logging
import time


class WasaltScraper:
    def __init__(
        self,
        base_url,
        mongo_uri="mongodb://localhost:27017/",
        db_name="wasalt",
        collection_name="properties",
        last_page=221,
    ):
        self.base_url = base_url
        self.last_page = last_page
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def fetch_page(self, url):
        """Fetch the HTML content of a page"""
        logging.info(f"Fetching: {url}")
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.text

    def parse_urls(self, html_content):
        """Extract property URLs using XPath"""
        tree = html.fromstring(html_content)
        urls = tree.xpath("//div[contains(@class,'styles_cardContent__jdYxS')]/a/@href")
        # Make full URLs if relative
        full_urls = [u if u.startswith("http") else f"https://wasalt.sa{u}" for u in urls]
        return full_urls

    def save_to_mongo(self, urls):
        """Insert property URLs into MongoDB (avoiding duplicates)"""
        for url in urls:
            if not self.collection.find_one({"url": url}):
                self.collection.insert_one({"url": url})
                logging.info(f"Saved: {url}")
            else:
                logging.info(f"Already exists: {url}")

    def run(self):
        """Main execution method with pagination"""
        for page in range(1, self.last_page + 1):
            paginated_url = f"{self.base_url}&page={page}"
            try:
                html_content = self.fetch_page(paginated_url)
                urls = self.parse_urls(html_content)
                self.save_to_mongo(urls)
                logging.info(f"Page {page}: {len(urls)} URLs processed.")
                time.sleep(1)  # polite delay
            except Exception as e:
                logging.error(f"Error processing page {page}: {e}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    url = "https://wasalt.sa/en/sale/search?propertyFor=sale&countryId=1&cityId=273&type=residential"
    scraper = WasaltScraper(url, last_page=221)
    scraper.run()
