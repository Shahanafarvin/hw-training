#!/usr/bin/env python3
import logging
import time
from lxml import html
from pymongo import MongoClient
from playwright.sync_api import sync_playwright


class SeLogerDetailScraper:
    def __init__(self, mongo_uri="mongodb://localhost:27017/",
                 db_name="seloger", urls_collection="apartments", details_collection="apartment_details"):
        # MongoDB
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.urls_col = self.db[urls_collection]
        self.details_col = self.db[details_collection]

    def parse_listing(self, page, url):
        """Extract the required fields from a listing page."""
        try:
            page.goto(url, timeout=30000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(2)  # wait for dynamic content

            # Try clicking "show phone" button if present
            try:
                phone_button = page.query_selector('xpath=//button[@aria-label="Tel"]')
                if phone_button:
                    phone_button.click()
                    time.sleep(2)  # give time for number to render
            except Exception:
                pass

            # Get HTML after clicking
            tree = html.fromstring(page.content())
            data = {"listing_url": url}

            # Seller phone
            seller_phone = tree.xpath('//button[@class="css-1ae1y8o"]//text()')
            data["seller_phone"] = seller_phone[0].strip() if seller_phone else None

            # Seller email
            seller_email = tree.xpath('//a[contains(@href,"mailto:")]/text()')
            data["seller_email"] = seller_email[0].strip() if seller_email else None

            # Property type
            property_type = tree.xpath('//span[contains(@class,"css-1b9ytm")]/text()')
            data["property_type"] = property_type[0].strip() if property_type else None

            # Property size
            property_size = tree.xpath('//div[contains(@class,"css-7tj8u")]//text()')
            data["property_size"] = property_size[4].strip() if property_size else None

            # Property price
            property_price = tree.xpath('//span[contains(@class,"css-otf0vo")]//text()')
            data["property_price"] = property_price[0].replace("€", "").strip() if property_price else None

            # City (static from your original search)
            data["city"] = "Franconville"

            return data

        except Exception as e:
            logging.error(f"Error parsing {url}: {e}")
            return None

    def save_to_mongo(self, data):
        if data:
            if not self.details_col.find_one({"listing_url": data["listing_url"]}):
                self.details_col.insert_one(data)
                logging.info(f"Saved details for {data['listing_url']}")
            else:
                logging.info(f"Already saved {data['listing_url']}")

    def run(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # set True if you want headless
            page = browser.new_page()

            urls_cursor = self.urls_col.find()
            for doc in urls_cursor:
                url = doc.get("url")
                if not url:
                    continue
                logging.info(f"Processing {url}")
                data = self.parse_listing(page, url)
                self.save_to_mongo(data)

            browser.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    scraper = SeLogerDetailScraper()
    scraper.run()
