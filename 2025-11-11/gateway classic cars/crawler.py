import time
from parsel import Selector
from curl_cffi import requests
from mongoengine import connect
from settings import logging, MONGO_DB
from items import ProductUrlItem


class Crawler:
    """Crawling vehicle URLs from Gateway Classic Cars"""

    def __init__(self):
        connect(db=MONGO_DB, alias='default', host='localhost', port=27017)

    def start(self):
        """Requesting Start URL"""
        url = "https://www.gatewayclassiccars.com/cars?max_year=1990&min_year=1914"
        meta = {"category": "Classic Cars", "page": 1}

        while True:
            response = requests.get(url, impersonate="chrome110", timeout=10)
            logging.info(f"Fetching: {url} | Status: {response.status_code}")

            if response.status_code == 200:
                is_next = self.parse_item(response, meta)
                if not is_next:
                    logging.info("Pagination completed.")
                    break

                # Find next page
                sel = Selector(response.text)
                next_page = sel.xpath("//a[@rel='next']/@href").get()
                if next_page:
                    url = next_page
                    meta["page"] += 1
                    time.sleep(1.5)
                else:
                    break
            else:
                logging.warning(f"Request failed for {url}")
                break

    def parse_item(self, response, meta):
        """Extract product URLs"""
        sel = Selector(response.text)

        PRODUCT_XPATH = "//div[@class='col-12 col-md-5 px-3']//a[starts-with(@href, 'https://www.gatewayclassiccars.com/vehicle')]/@href"
        product_links = sel.xpath(PRODUCT_XPATH).getall()

        if product_links:
            for link in product_links:
                item = {"url": link.strip()}
                try:
                    product_item = ProductUrlItem(**item)
                    product_item.save()
                except Exception as e:
                    logging.warning(f"Mongo insert failed: {e}")
            return True
        return False

    def close(self):
        """Close function for cleanup"""
        logging("Url Extraction Completed")


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()
