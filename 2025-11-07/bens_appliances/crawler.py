import logging
import requests
from parsel import Selector
from mongoengine import connect
from settings import BASE_URL, MONGO_DB, HEADERS
from items import ProductUrlItem


class Crawler:
    """Crawls product listing pages and stores product URLs in MongoDB"""

    def __init__(self):
        connect(db=MONGO_DB, alias='default', host='localhost', port=27017)

    def start(self):
        """Start crawling from /collections/all"""
        start_url = f"{BASE_URL}/collections/all"
        next_url = start_url
        count = 0

        while next_url:
            try:
                logging.info(f"Fetching page: {next_url}")
                response = requests.get(next_url, headers=HEADERS)

                if response.status_code != 200:
                    logging.warning(f"Failed to fetch {next_url} | Status: {response.status_code}")
                    break

                sel = Selector(response.text)

                # Extract product URLs
                product_links = sel.xpath("//div[@class='product-item product-item--vertical   1/3--tablet-and-up 1/4--desk']/a/@href").getall()
                product_links = [
                    BASE_URL + link if link.startswith("/") else link
                    for link in product_links
                ]

                for link in product_links:
                    try:
                        product_url_item = ProductUrlItem(url=link)
                        product_url_item.save()
                        logging.info(f"Inserted product URL: {link}")
                        count += 1
                    except Exception as e:
                        logging.error(f"Error saving URL {link}: {e}")

                # Pagination
                next_page = sel.xpath("//a[@class='pagination__next link']/@href").get()
                if next_page:
                    next_url = BASE_URL + next_page if next_page.startswith("/") else next_page
                else:
                    logging.info("No more pages found.")
                    break

            except Exception as e:
                logging.error(f"Error processing page {next_url}: {e}")
                break

        logging.info(f"Crawling completed. Total URLs collected: {count}")

    def close(self):
        logging.info("Crawler finished successfully.")


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()
