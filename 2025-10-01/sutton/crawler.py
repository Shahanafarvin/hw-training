#!/usr/bin/env python3
import logging
from urllib.parse import urljoin

from pymongo import MongoClient
from playwright.sync_api import sync_playwright


class SuttonAgentScraper:
    BASE_URL = "https://sutton.com/ca/agent"
    MAX_PAGE = 224

    def __init__(self, mongo_uri="mongodb://localhost:27017/", db_name="sutton", collection_name="agents"):
        # MongoDB setup
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def save_links(self, links):
        """Insert links into MongoDB if not already present."""
        for link in links:
            if not self.collection.find_one({"url": link}):
                self.collection.insert_one({"url": link})
                logging.info(f"Inserted: {link}")
            else:
                logging.debug(f"Duplicate skipped: {link}")

    def scrape_page(self, page, page_num):
        """Scrape a single page for agent links using XPath."""
        url = f"{self.BASE_URL}?page={page_num}"
        logging.info(f"Scraping page {page_num}: {url}")
        page.goto(url, timeout=60000)
        page.wait_for_selector("a[href*='/ca/agent/']")  # ensure JS content loaded

        # XPath query
        elements = page.locator("//a[contains(@href, '/ca/agent/')]").all()
        links = [urljoin(self.BASE_URL, el.get_attribute("href")) for el in elements if el.get_attribute("href")]
        return list(set(links))

    def run(self):
        """Main execution with Playwright browser session."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            for i in range(1, self.MAX_PAGE + 1):
                try:
                    links = self.scrape_page(page, i)
                    if links:
                        self.save_links(links)
                    else:
                        logging.warning(f"No links found on page {i}")
                except Exception as e:
                    logging.error(f"Error scraping page {i}: {e}")

            browser.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = SuttonAgentScraper()
    scraper.run()
