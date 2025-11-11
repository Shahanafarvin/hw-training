import logging
import requests
import time
from parsel import Selector
from datetime import datetime
from items import ProductUrlItem, CategoryItem
from settings import HEADERS, REQUEST_DELAY, MONGO_CONNECTION

class Crawler:
    """Crawling product listing pages (per subcategory) and saving product URLs only"""

    def __init__(self):
        self.mongo = MONGO_CONNECTION

    def start(self):
        """Read categories from DB and crawl each subcategory for product urls"""
        logging.info("Starting product URL crawler...")

        # iterate through categories saved by CategoryCrawler
        for cat_doc in CategoryItem.objects:
            category = cat_doc.category
            for sub in cat_doc.subcategories:
                sub_name = sub.get("name")
                sub_url = sub.get("url")
                if not sub_url:
                    continue

                logging.info(f"Processing subcategory: {category} -> {sub_name} ({sub_url})")
                try:
                    # crawl pagination for sub_url
                    self.parse_item(category, sub_name, sub_url)
                except Exception as e:
                    logging.exception(f"Error crawling {sub_url}: {e}")

    def parse_item(self, category, sub_name, start_url):
        """Extract product links with pagination"""
        next_page = start_url
        while next_page:
            logging.info(f"Fetching product list page: {next_page}")
            resp = requests.get(next_page, headers=HEADERS)
            if resp.status_code != 200:
                logging.warning(f"Failed to fetch {next_page} ({resp.status_code})")
                break

            sel = Selector(resp.text)

            products = sel.xpath("//a[@class='imglink']/@href").getall()
            for link in products:
                if not link:
                    continue
                # save each product url as a ProductUrlItem document
                try:
                    pu = ProductUrlItem(
                        category=category,
                        subcategory=sub_name,
                        url=link,
                    )
                    pu.save()
                    logging.info(f"Saved product URL: {link}")
                except Exception as e:
                    logging.exception(f"Failed to save product url {link}: {e}")
                    
            next_rel = sel.xpath("//div[@class='pagination-arrows']//a[img/@alt='next page']/@href").get()
            if next_rel:
                next_page = next_rel.strip()
            else:
                logging.info("No next page found for this subcategory.")
                break

            time.sleep(REQUEST_DELAY)

    def close(self):
        logging.info("Crawler closed.")


if __name__ == "__main__":
    c = Crawler()
    c.start()
    c.close()
