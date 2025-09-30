#!/usr/bin/env python3
import logging
import time
from urllib.parse import urljoin

import requests
from lxml import html
from pymongo import MongoClient, ASCENDING

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


class FressnapfScraper:
    BASE_URL = "https://www.fressnapf.de/"

    # Use homepage-only XPaths to locate nodes (we only follow sub-subcategory URLs)
    XPATH_CATEGORY_NODES = "//li[contains(@id,'level1-item-')]"
    XPATH_SUBCATEGORY_NODES = "//li[contains(@id,'level2-item-')]"
    XPATH_SUBSUBCATEGORY_NODES = "//li[contains(@id,'level3-item-')]/a"
   

    # Product page xpaths (used when visiting sub-subcategory pages)
    XPATH_PRODUCT_LINKS = "//div[contains(@class,'product-teaser')]//a[@href]/@href"
    XPATH_NEXT_PAGE = "//a[@id='pagination-nextPage']/@href"

    def __init__(
        self,
        proxy_string: str,
        mongo_uri: str = "mongodb://localhost:27017/",
        db_name: str = "fressnapf",
        request_delay: float = 0.6,
    ):
        self.session = requests.Session()
        self.session.proxies.update({"https": proxy_string})
        # follow your example: disable TLS verification if needed
        self.session.verify = False
        self.delay = request_delay

        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]

        # Ensure an index to avoid duplicate products
        self.db.products.create_index([("product_url", ASCENDING)], unique=True)

    def fetch_tree(self, url):
        """Fetch a URL and return an lxml tree or None on failure."""
        try:
            logging.info("GET %s", url)
            resp = self.session.get(url, timeout=60)
            resp.raise_for_status()
            return html.fromstring(resp.text)
        except Exception as e:
            logging.warning("Failed to fetch %s : %s", url, e)
            return None
        finally:
            time.sleep(self.delay)

    def parse_homepage(self):
        """Parse homepage nodes and build a nested structure with correct category -> subcategory mapping."""
        tree = self.fetch_tree(self.BASE_URL)
        if tree is None:
            logging.error("Couldn't fetch homepage.")
            return []

        categories = []

        # get all category nodes and all subcategory blocks (parallel lists)
        cat_nodes = tree.xpath(self.XPATH_CATEGORY_NODES)
        subcat_blocks = tree.xpath("//ul[contains(@class,'nav-level-2')]")

        for idx, cat_node in enumerate(cat_nodes):
            category_name = cat_node.xpath(".//text()")
            subcategories = []

            # map this category to the corresponding subcategory block (same index)
            if idx < len(subcat_blocks):
                block = subcat_blocks[idx]

                for sub_node in block.xpath("./li"):
                    subcat_name = sub_node.xpath(".//text()")
                    subcat_href = sub_node.xpath(".//a/@href")
                    subcat_url = urljoin(self.BASE_URL, subcat_href[0]) if subcat_href else None

                    subsubcats = []
                    for s3 in sub_node.xpath(".//li[contains(@id,'level3-item-')]/a"):
                        s3_name = " ".join(s3.xpath(".//text()")).strip()
                        s3_href = s3.get("href")
                        s3_url = urljoin(self.BASE_URL, s3_href) if s3_href else None
                        subsubcats.append({"name": s3_name, "url": s3_url})

                    subcategories.append({
                        "name": subcat_name,
                        "url": subcat_url,
                        "subsubcategories": subsubcats
                    })

            categories.append({
                "name": category_name,
                "subcategories": subcategories
            })

        return categories



    def parse_products_from_subsub(self, subsub_url):
        """Visit a sub-subcategory page and paginate to collect product URLs (returns list of absolute URLs)."""
        if not subsub_url:
            return []

        found = set()
        next_page = subsub_url

        while next_page:
            tree = self.fetch_tree(next_page)
            if tree is None:
                break

            links = tree.xpath(self.XPATH_PRODUCT_LINKS)
            for href in links:
                if not href:
                    continue
                full = urljoin(self.BASE_URL, href.strip())
                found.add(full)

            # find next page
            nexts = tree.xpath(self.XPATH_NEXT_PAGE)
            if nexts:
                next_page = urljoin(self.BASE_URL, nexts[0])
                logging.info("Next page found -> %s", next_page)
            else:
                next_page = None

        return list(found)

    def save_categories(self, categories):
        """Store entire hierarchy into `categories` collection (overwrite for simple runs)."""
        if not categories:
            return
        # Replace existing doc to keep single hierarchy doc (or you can change to insert_many)
        self.db.categories.delete_many({})  # simple reset; remove if you want incremental
        self.db.categories.insert_many(categories)
        logging.info("Saved %d top-level categories to `categories` collection.", len(categories))

    def save_products(self, product_docs):
        """Upsert product documents into `products` collection."""
        if not product_docs:
            return

        for doc in product_docs:
            try:
                # upsert by product_url to avoid duplicates
                self.db.products.update_one(
                    {"product_url": doc["product_url"]},
                    {"$setOnInsert": doc},
                    upsert=True,
                )
            except Exception as e:
                logging.warning("Failed to upsert %s : %s", doc.get("product_url"), e)
        logging.info("Upsert attempted for %d product documents.", len(product_docs))

    def scrape_all(self):
        """Main flow: parse homepage structure, save it, then iterate subcategory/sub-subcategory URLs and save product URLs."""
        logging.info("Parsing homepage for category hierarchy...")
        categories = self.parse_homepage()
        if not categories:
            logging.error("No categories extracted; aborting.")
            return
        self.save_categories(categories)

        # For each subcategory / sub-subcategory found on homepage, extract product URLs and save
        total_products = 0
        product_docs = []

        for cat in categories:
            cat_name = cat["name"]
            for sub in cat["subcategories"]:
                sub_name = sub["name"]

                # case 1: sub-subcategories exist
                if sub["subsubcategories"]:
                    for s3 in sub["subsubcategories"]:
                        s3_name = s3["name"]
                        s3_url = s3["url"]
                        logging.info("Collecting products for: %s > %s > %s (%s)",
                                     cat_name, sub_name, s3_name, s3_url)
                        urls = self.parse_products_from_subsub(s3_url)
                        total_products += len(urls)
                        for p in urls:
                            product_docs.append(
                                {
                                    "category": cat_name,
                                    "subcategory": sub_name,
                                    "subsubcategory": s3_name,
                                    "subsubcategory_url": s3_url,
                                    "product_url": p,
                                }
                            )

                        if len(product_docs) >= 200:
                            self.save_products(product_docs)
                            product_docs = []

                # case 2: no sub-subcategories -> scrape directly from subcategory URL
                else:
                    s_url = sub.get("url")
                    if not s_url:
                        continue
                    logging.info("Collecting products for: %s > %s (no sub-subcategories, using subcat URL: %s)",
                                 cat_name, sub_name, s_url)
                    urls = self.parse_products_from_subsub(s_url)
                    total_products += len(urls)
                    for p in urls:
                        product_docs.append(
                            {
                                "category": cat_name,
                                "subcategory": sub_name,
                                "subsubcategory": None,
                                "subsubcategory_url": None,
                                "subcategory_url": s_url,
                                "product_url": p,
                            }
                        )

                    if len(product_docs) >= 200:
                        self.save_products(product_docs)
                        product_docs = []

        # save any remaining
        if product_docs:
            self.save_products(product_docs)

        logging.info("Scraping finished. Total product URLs discovered (attempted insert): %d", total_products)



if __name__ == "__main__":
    PROXY = "scraperapi.follow_redirect=false.retry_404=true.country_code=de.device_type=desktop.session_number=112:dbed3523ea977273dc3a388415c0aff1@proxy-server.scraperapi.com:8001"

    scraper = FressnapfScraper(proxy_string=PROXY, mongo_uri="mongodb://localhost:27017/", db_name="fressnapf")
    scraper.scrape_all()
