import time
from parsel import Selector
from curl_cffi import requests
from mongoengine import connect
import re
from settings import logging, MONGO_DB, BASE_URL
from items import CategoryItem  


START_URL = f"{BASE_URL}/ae_en"


class CategoryCrawler:
    """Crawl Matalanme categories, subcategories, and UIDs"""

    def __init__(self):
        connect(db=MONGO_DB, alias='default', host='localhost', port=27017)

    def get_selector(self, url):
        """Fetch page and return Selector."""
        try:
            response = requests.get(url, impersonate="chrome110", timeout=20)
            if response.status_code == 200:
                return Selector(response.text)
            logging.warning(f"Failed {response.status_code}: {url}")
        except Exception as e:
            logging.error(f"Error fetching {url}: {e}")
        return None

    # ------------------------------------------------------
    # Extract categories + subcategories
    # ------------------------------------------------------
    def parse_subcategories(self):
        sel = self.get_selector(START_URL)
        if not sel:
            return []

        # Categories
        category_nodes = sel.xpath("//li[contains(@class,'categoryRoundWidget_tab_item__usuFC ')]/button")
        categories = [c.xpath("string()").get().strip().lower() for c in category_nodes]
        logging.info(f"Found {len(categories)} categories")

        # Subcategories
        subcategory_nodes = sel.xpath("//div[@class='categoryRoundWidget_tab_content_item__WyDCH']")
        all_subcats = []
        for div in subcategory_nodes:
            for a in div.xpath("./a"):
                href = a.xpath("@href").get()
                text = a.xpath("normalize-space(.)").get(default="").strip().lower()
                if not href or not text:
                    continue
                full_href = BASE_URL + href if href.startswith("/") else href
                all_subcats.append({"name": text, "href": full_href})

        # Map subcategories to categories
        final_structure = []
        for category_name in categories:
            matched_subcats = []
            for sub in all_subcats:
                if f"/{category_name}/" in sub["href"]:
                    matched_subcats.append({
                        "sub_category_name": sub["name"],
                        "sub_category_url": sub["href"]
                    })
            final_structure.append({
                "category_name": category_name,
                "subcategories": matched_subcats
            })

        return final_structure

    # ------------------------------------------------------
    # Extract UID(s)
    # ------------------------------------------------------
    def parse_uid(self, sub_url):
        sel = self.get_selector(sub_url)
        if not sel:
            return None

        script_text = sel.xpath('//script[contains(text(),"categoryData")]/text()').get()
        if not script_text:
            return None

        # Remove push wrapper
        payload = script_text.replace('self.__next_f.push([1,"1e:[[\"$\",\"$L1f\",null,', '')
        payload = payload.replace(']","$L21"])', '')

        # Decode escaped characters
        payload = payload.encode('utf-8').decode('unicode_escape')
        payload = payload.replace("\\/", "/")

        # Extract UID(s)
        uids = re.findall(r'"uid"\s*:\s*"([^"]+)"', payload)
        return uids if uids else None

    # ------------------------------------------------------
    # Main crawling logic
    # ------------------------------------------------------
    def start(self):
        categories = self.parse_subcategories()
        for category in categories:
            logging.info(f"Processing Category: {category['category_name']}")
            subcat_list = []
            for sub in category["subcategories"]:
                time.sleep(1)  # polite delay
                uids = self.parse_uid(sub["sub_category_url"])
                item_data = {
                    "category_name": category["category_name"],
                    "sub_category_name": sub["sub_category_name"],
                    "sub_category_url": sub["sub_category_url"],
                    "uids": uids
                }

                # Save using MongoEngine item
                try:
                    cat_item = CategoryItem(**item_data)
                    cat_item.save()
                except Exception as e:
                    logging.warning(f"Mongo insert failed: {e}")

                subcat_list.append(item_data)

            logging.info(f"Completed Category: {category['category_name']} with {len(subcat_list)} subcategories")

    def close(self):
        logging.info("Matalanme Crawling Completed")


if __name__ == "__main__":
    crawler = CategoryCrawler()
    crawler.start()
    crawler.close()
