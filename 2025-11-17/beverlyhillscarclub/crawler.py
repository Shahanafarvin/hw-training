import requests
from parsel import Selector
from mongoengine import connect
from items import PeoductURLItem
from settings import MONGO_DB, BASE_URL, HEADERS, LIMIT, MAX_CARS
import logging


class Crawler:
    def __init__(self):
        connect(db=MONGO_DB, host="localhost", alias="default", port=27017)

    def start(self):
        logging.info("Crawler started...")
        total_saved = 0

        for offset in range(0, MAX_CARS, LIMIT):
            params = {
                "module": "inventory",
                "sold": "Available",
                "future_inventory": "!1",
                "pending_sale": "!1",
                "pending": "!1",
                "limit": str(LIMIT),
                "orderby": "make,year",
                "offset": str(offset),
            }

            response = requests.get(BASE_URL, headers=HEADERS, params=params)

            product_urls = self.parse_item(response.text)

            for url in product_urls:
                PeoductURLItem(url=url).save()
                total_saved += 1

        logging.info(f"Saved total {total_saved} URLs.")

    def parse_item(self, response_text):
        """
        Extract product URLs from the PLP HTML inside API response.
        Returns a list of complete URLs.
        """
        sel = Selector(response_text)
        urls = sel.xpath("//a[img[@class='img-responsive']]/@href").getall()
        
        return urls

# ------------------ MAIN ENTRY POINT ------------------
if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
