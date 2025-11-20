import logging
from mongoengine import connect
from curl_cffi import requests
from parsel import Selector
from items import CategoryUrlItem
from settings import HOMEPAGE_HEADERS, MONGO_DB, BASE_HOMEPAGE


class Crawler:
    """Crawling Urls"""

    def __init__(self):
        self.mongo = connect(db=MONGO_DB, host="localhost", alias="default")

    def start(self):
        """Requesting Start url"""
        meta = {}
        meta['category'] = BASE_HOMEPAGE

        logging.info("Fetching homepage to extract category names...")

        response = requests.get(BASE_HOMEPAGE, headers=HOMEPAGE_HEADERS, impersonate="chrome")

        if response.status_code in [200,404]:
            self.parse_item(response, meta)


    def parse_item(self, response, meta):
        """item part"""

        sel = Selector(response.text)

        # XPATH
        CATEGORY_XPATH = "(//ul[@class='row list-unstyled'])[1]/li"
        CATEGORY_URL_XPATH = ".//ul/li/a/@href"

        # EXTRACT
        items = sel.xpath(CATEGORY_XPATH)
        if items:
            for li in items[:3]:
                category_urls = li.xpath(CATEGORY_URL_XPATH).getall()

                for href in category_urls:
                    part = href.rstrip("/").split("/")[-1]
                    part = part.split("?")[0].strip()
                    print(part)
                    if not part:
                        continue

                    # ITEM YEILD
                    item = {}
                    item['category'] = part
                    logging.info(item)
                    try:
                        CategoryUrlItem(**item).save()
                    except:
                        pass

            logging.info(f"Categories extraction completed")
            return True

        return False

    def close(self):
        """Close function for all module object closing"""

        self.mongo.close()


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()