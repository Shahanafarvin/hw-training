import logging
from curl_cffi import requests
from parsel import Selector
from pymongo import MongoClient
from settings import ( 
    BASE_URL, 
    MONGO_DB,
    MONGO_COLLECTION_CATEGORY,
    MONGO_COLLECTION_PRODUCTS,
)
#from items import ProductUrlItem


class Crawler:
    """Crawling Product URLs from Max Fashion"""

    def __init__(self):
        self.mongo = MongoClient("localhost", 27017)
        self.db = self.mongo[MONGO_DB]

    def start(self):

        for category in self.db[MONGO_COLLECTION_CATEGORY].find():

            cat_name = category.get("name")

            for subcat in category.get("subcategories", []):
                subcat_name = subcat.get("name")

                for final in subcat.get("subsubcategories", []):
                    final_name = final.get("name")
                    final_url  = final.get("url")

                    logging.info(f"Visiting: {cat_name} → {subcat_name} → {final_name}")

                    meta = {
                        "category": f"{cat_name} → {subcat_name} → {final_name}",
                        "url": final_url,
                        "page": 1,
                        "last_page": None,  # will be filled inside parse_item()
                    }

                    # Crawl page-by-page
                    while True:

                        # First page → original URL
                        if meta["page"] == 1:
                            page_url = final_url
                        else:
                            page_url = f"{final_url}?p={meta['page']}"

                        logging.info(f"Page {meta['page']} : {page_url}")

                       
                        response = requests.get(page_url, impersonate="chrome")

                        if response.status_code != 200:
                            logging.error(f"Failed to load page {meta['page']}")
                            break

                        is_next = self.parse_item(response, meta)

                        if not is_next:
                            logging.info("No more products → stopping pagination.")
                            break

                        # If first page, parse_item() sets last_page
                        if meta["last_page"] is None:
                            meta["last_page"] = 1  # fallback
                        
                        # Stop when page > last_page
                        if meta["page"] >= meta["last_page"]:
                            logging.info("Reached last page.")
                            break

                        meta["page"] += 1


    def parse_item(self, response, meta):
        """Parse product URLs + extract last page here"""

        sel = Selector(response.text)
        #xpath
        LAST_PAGE_XPATH = '//ul[contains(@class,"jss")]/li[last()-1]//text()'
        PRODUCT_URL_XPATH = '//a[contains(@id,"prodItemImgLink")]/@href'

        # Extract last page only on 1st page
        if meta["page"] == 1:
            
            last_page = sel.xpath(LAST_PAGE_XPATH).get()

            try:
                last_page = int(last_page)
            except:
                last_page = 1

            meta["last_page"] = last_page
            logging.info(f"Detected last page: {last_page}")

        # Extract product URLs
        products = sel.xpath(PRODUCT_URL_XPATH).getall()

        if not products:
            return False

        for product_path in products:
            url = f"{BASE_URL}{product_path}"

            # ITEM YIELD
            item = {}
            item['url'] = url
            
            logging.info(item)
                
            try:
                self.db[MONGO_COLLECTION_PRODUCTS].insert_one(item)
            except:
                pass
        return True


    def close(self):
        self.mongo.close()


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()
