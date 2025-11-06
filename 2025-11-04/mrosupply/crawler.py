import logging
import time
import requests
from parsel import Selector
from items import CategoryItem, ProductUrlItem
from settings import BASE_URL, MONGO_DB, logging
from mongoengine import connect 


class Crawler:
    """Crawling Product URLs from leaf categories"""

    def __init__(self):
        connect(db=MONGO_DB, alias='default', host='localhost', port=27017)

    def start(self):
        """Iterate all main categories and extract product URLs from leaf categories"""

        all_categories = CategoryItem.objects()  # fetch saved categories

        for main_cat in all_categories:
            logging.info(f"Processing main category: {main_cat.name}")

            # Convert MongoEngine doc to dict for recursion
            cat_dict = {
                "name": main_cat.name,
                "url": main_cat.url,
                "subcategories": main_cat.subcategories
            }

            # Traverse leaf categories
            stack = [cat_dict]
            while stack:
                node = stack.pop()

                if "subcategories" in node and node["subcategories"]:
                    stack.extend(node["subcategories"])
                else:
                    logging.info(f"Extracting products from leaf: {node['name']}")
                    products = []
                    next_page_url = node["url"]

                    while next_page_url:
                        try:
                            response = requests.get(next_page_url, headers={
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                            }, timeout=30)

                            if response.status_code != 200:
                                logging.warning(f"Skipped ({response.status_code}): {next_page_url}")
                                break

                            sel = Selector(response.text)

                            # Extract product URLs
                            urls = sel.xpath('//a[@class="m-catalogue-product-title js-product-link"]/@href').getall()
                            urls = [BASE_URL + p.strip() for p in urls]
                            products.extend(urls)

                            # Pagination
                            next_link = sel.xpath('//a[@aria-label="Go to next page"]/@href').get()
                            if next_link:
                                next_page_url = BASE_URL + next_link.strip()
                                time.sleep(1)
                            else:
                                next_page_url = None

                        except Exception as e:
                            logging.error(f"Error fetching {next_page_url}: {e}")
                            break

                    # Save to MongoDB one by one (category-wise)
                    try:
                        ProductUrlItem(
                            category_name=node["name"],
                            category_url=node["url"],
                            product_urls=products
                        ).save()
                        logging.info(f" Saved {len(products)} products for category: {node['name']}")
                    except Exception as e:
                        logging.error(f" Error saving product URLs for {node['name']}: {e}")


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
   
