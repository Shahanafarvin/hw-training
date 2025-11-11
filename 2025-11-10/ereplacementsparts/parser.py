import logging
import requests
import time
from parsel import Selector
from items import ProductUrlItem, ProductItem
from settings import HEADERS, REQUEST_DELAY, MONGO_CONNECTION

class Parser:
    """Parser reads product URLs from DB and saves product details using ProductItem(**item)"""

    def __init__(self):
        self.mongo = MONGO_CONNECTION

    def start(self):
        # iterate all ProductUrlItem documents
        for url_doc in ProductUrlItem.objects:
            url = url_doc.url
            logging.info(f"Parsing: {url}")

            try:
                self.parse_item(url)
            except Exception as e:
                logging.exception(f"Failed to parse {url}: {e}")
            time.sleep(REQUEST_DELAY)

    def parse_item(self, url):
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            logging.warning(f"Failed to fetch {url} ({resp.status_code})")
            return

        sel = Selector(resp.text)

        # XPATHs 
        breadcrumbs = sel.xpath("//div[@class='crumbs d-flex align-items-center']//span[@itemprop='name' or @class='mach-breadcrumb']/text()").getall()
        name = sel.xpath("//h1/text()").get()
        oem_part_for = sel.xpath("//span[@itemprop='brand']/text()").get()
        part_number = sel.xpath("//span[@itemprop='mpn']/text()").get()
        price = sel.xpath("//span[@itemprop='price']/text()").get()
        availability = sel.xpath("//span[@temprop='availability']/text()").get()
        description = " ".join(sel.xpath("//div[@id='primary_desc']//text()").getall())
        additional_description = " ".join(sel.xpath("//ul[@class='add_desc']//text()").getall())

        item = {
            "url": url,
            "breadcrumbs": breadcrumbs,
            "product_name": name,
            "price": price,
            "oem_part_for": oem_part_for,
            "part_number": part_number,
            "availability": availability,
            "description":description,
            "additional_description": additional_description,
        }

        # Save using ProductItem mongoengine model
        try:
            product_item = ProductItem(**item)
            product_item.save()
            logging.info(f"Saved product: {item.get('product_name') or item.get('url')}")
        except Exception as e:
            logging.exception(f"Failed to save product item for {url}: {e}")

    def close(self):
        logging.info("Parser closed.")


if __name__ == "__main__":
    parser = Parser()
    parser.start()
    parser.close()
