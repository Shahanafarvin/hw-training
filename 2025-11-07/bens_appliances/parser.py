import logging
import requests
from parsel import Selector
from mongoengine import connect
from settings import HEADERS, MONGO_DB
from items import ProductItem, ProductUrlItem


class Parser:
    """Parses product detail pages and saves data using ProductItem"""

    def __init__(self):
        connect(db=MONGO_DB, alias='default', host='localhost', port=27017)

    def start(self):
        """Start parsing product URLs from DB"""
        urls = [doc.url for doc in ProductUrlItem.objects]
        logging.info(f"Total URLs to parse: {len(urls)}")

        for url in urls:
            try:
                logging.info(f"Scraping: {url}")
                response = requests.get(url, headers=HEADERS, timeout=20)

                if response.status_code != 200:
                    logging.warning(f"Failed to fetch {url} | Status: {response.status_code}")
                    continue

                self.parse_item(url, response)
            except Exception as e:
                logging.error(f"Error parsing {url}: {e}")

        logging.info("Parsing completed successfully.")

    def parse_item(self, url, response):
        """Extract and save product details"""
        sel = Selector(response.text)
        title=sel.xpath('//h1/text()').get()
        manufacturer=sel.xpath('//a[@class="product-meta__vendor link link--accented"]/text()').get()
        price="".join(sel.xpath('//span[@class="price price--highlight"]//text() | //span[@class="price"]//text()').getall())
        description=" ".join(sel.xpath('//div[@class="rte text--pull"]//text()').getall())
        equivalent_part_numbers=",".join(sel.xpath('//div[@class="col-md-4"]//text()').getall())
        availability=True if sel.xpath('//button[@data-action="add-to-cart"]') else False
        image_urls=[
            img.strip() for img in sel.xpath(
                    '//div[@class="product-gallery product-gallery--with-thumbnails"]//img/@src'
                ).getall()
            ]
        item = {
            "url": url,
            "title": title,
            "manufacturer": manufacturer,
            "price": price,
            "description": description,
            "equivalent_part_numbers": equivalent_part_numbers,
            "availability":availability,
            "image_urls":image_urls,
        }

        # Clean and save using ProductItem model
        product_item = ProductItem(**item)
        try:
            product_item.save()
            logging.info(f"Saved product: {item.get('title', 'N/A')}")
        except Exception as e:
            logging.error(f"Failed to save product {url}: {e}")

    def close(self):
        logging.info("Parser finished successfully.")


if __name__ == "__main__":
    parser_obj = Parser()
    parser_obj.start()
    parser_obj.close()
