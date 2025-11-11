import logging
import requests
from parsel import Selector
from datetime import datetime
from items import CategoryItem
from settings import BASE_URL, HEADERS, MONGO_CONNECTION

class CategoryCrawler:
    """Crawling category and subcategory URLs and saving to Mongo (CategoryItem)"""

    def __init__(self):
       self.mongo = MONGO_CONNECTION

    def start(self):
        """Requesting Categories page and extracting categories"""
        url = f"{BASE_URL}/accessories-c-714.html"
        try:
            resp = requests.get(url, headers=HEADERS)
            if resp.status_code != 200:
                logging.error(f"Failed to fetch categories page: {resp.status_code}")
                return

            sel = Selector(resp.text)

            for cat in sel.xpath("//div[@class='product_listing']"):
                category_name = cat.xpath(".//div[@class='product_name']//a/text()").get()
                category_url = cat.xpath(".//div[@class='product_name']//a/@href").get()

                if not category_name or not category_url:
                    continue

                category_name = category_name.strip()
                subcategories = []
                for sub in cat.xpath(".//div[@class='subcategory-link']"):
                    sub_name = sub.xpath(".//a/span/text()").get()
                    sub_url = sub.xpath(".//a/@href").get()
                    if sub_name and sub_url:
                        subcategories.append({"name": sub_name.strip(), "url": sub_url.strip()})

                # Save using mongoengine model
                try:
                    doc = CategoryItem(
                        category=category_name,
                        url=category_url,
                        subcategories=subcategories,
                    )
                    doc.save()
                    logging.info(f"Inserted category: {category_name} ({len(subcategories)} subcats)")
                except Exception as e:
                    logging.exception(f"Failed to save category {category_name}: {e}")
        except Exception as e:
            logging.exception(f"Error in category extraction: {e}")

    def close(self):
        logging.info("CategoryCrawler closing (nothing to close).")


if __name__ == "__main__":
    crawler = CategoryCrawler()
    crawler.start()
    crawler.close()
