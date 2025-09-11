import requests
from parsel import Selector
from urllib.parse import urljoin
from pymongo import MongoClient
import time

BASE_URL = "https://www.next.co.uk/"

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["next_scraper"]
collection = db["crawler"]

def get_selector(url):
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return Selector(resp.text)

def scrape_categories():
    sel = get_selector(BASE_URL)
    categories = sel.css("nav a::attr(href)").getall()
    categories = [urljoin(BASE_URL, c) for c in categories if c.startswith("/")]
    return list(set(categories))

def scrape_subcategories(category_url):
    sel = get_selector(category_url)
    subcats = sel.css("a::attr(href)").getall()
    subcats = [urljoin(BASE_URL, s) for s in subcats if "/shop/" in s]
    return list(set(subcats))

def scrape_products(subcat_url):
    sel = get_selector(subcat_url)
    product_links = sel.css("a::attr(href)").getall()
    product_links = [urljoin(BASE_URL, p) for p in product_links if "/style/" in p]
    return list(set(product_links))

def main():
    categories = scrape_categories()
    print(f"Found {len(categories)} categories.")

    for cat_url in categories:
        print(f"Category: {cat_url}")
        category_dict = {}

        subcats = scrape_subcategories(cat_url)
        for subcat_url in subcats:
            print(f"  Subcategory: {subcat_url}")
            product_urls = scrape_products(subcat_url)
            category_dict[subcat_url] = product_urls
            time.sleep(1)  # polite delay

        # Insert into MongoDB
        if category_dict:
            collection.update_one(
                {"category_url": cat_url},
                {"$set": {"subcategories": category_dict}},
                upsert=True
            )
            print(f"Saved category {cat_url} to MongoDB")

if __name__ == "__main__":
    main()
