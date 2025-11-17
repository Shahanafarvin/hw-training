import requests
from parsel import Selector
from items import ProductUrlItem
from mongoengine import connect
from settings import HEADERS, MONGO_DB, logging
from time import sleep

class Crawler:
    """Crawling vehicle URLs"""

    def __init__(self):
        connect(db=MONGO_DB, host="localhost", alias="default", port=27017)

    def start(self):
        BASE = "https://www.stlouiscarmuseum.com"
        url = f"{BASE}/vehicles"

        while url:
            logging.info(f"Fetching page: {url}")
            response = requests.get(url, headers=HEADERS)
            if response.status_code != 200:
                logging.warning(f"Failed to fetch {url} (status {response.status_code})")
                break

            sel = Selector(response.text)
            links = sel.xpath("//a[@class='stlouis-list-item']/@href").getall()

            for link in links:
                full_url = BASE + link if link.startswith("/") else link
                try:
                    ProductUrlItem(url=full_url).save()
                    logging.info(f"Saved URL: {full_url}")
                except:
                    logging.info(f"URL already exists: {full_url}")

            next_page = sel.xpath("//a[@rel='next']/@href").get()
            url = BASE + next_page if next_page and next_page.startswith("/") else next_page
            sleep(1)

        logging.info("Crawler finished")

if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
