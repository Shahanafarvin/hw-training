import requests
from parsel import Selector
import time
from items import CategoryItem
from settings import MONGO_DB, BASE_URL, logging
from mongoengine import connect


connect(db=MONGO_DB, alias='default', host='localhost', port=27017)

# -----------------------
# Helper: Request and parse safely
# -----------------------
def fetch_selector(url):
    """Fetch page and return Selector object."""
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            logging.warning(f"Skipped ({resp.status_code}): {url}")
            return None
        return Selector(resp.text)
    except Exception as e:
        logging.error(f"Error fetching {url}: {e}")
        return None


# -----------------------
# Recursive function to extract subcategories
# -----------------------
def extract_subcategories(url, depth=1):
    sel = fetch_selector(url)
    if not sel:
        return []

    subcategories = []

    category_blocks = sel.xpath('//div[contains(@class,"lp-flex lp-flex--no-wrap")]')
    if not category_blocks:
        return []

    indent = "    " * depth
    for div in category_blocks:
        href = div.xpath('.//a/@href').get()
        sub_name = div.xpath('.//p[contains(@class,"category--title")]/text()').get()

        if not href or not sub_name:
            continue

        href = href.strip()
        sub_name = sub_name.strip()
        if href.startswith("/"):
            href = BASE_URL.rstrip("/") + href

        logging.info(f"{indent}↳ {sub_name}")

        sub_subcats = extract_subcategories(href, depth + 1)

        subcategories.append({
            "name": sub_name,
            "url": href,
            "subcategories": sub_subcats
        })

        time.sleep(1)

    return subcategories


# -----------------------
# Step 1: Extract main categories
# -----------------------
response = requests.get(BASE_URL)
response.raise_for_status()
sel = Selector(response.text)

main_categories = []
for cat in sel.xpath('//li[contains(@class,"o-categories-list--item")]/a'):
    url = cat.xpath('./@href').get()
    if url:
        url = url.strip()
        full_href = BASE_URL.rstrip("/") + url
        name = url.replace("/", "").replace("-", " ").strip().title()
        main_categories.append({"name": name, "url": full_href})

logging.info(f"✅ Found {len(main_categories)} main categories")

# -----------------------
# Step 2: Build recursive category tree
# -----------------------
category_tree = []
for cat in main_categories:
    logging.info(f"Processing main category: {cat['name']} → {cat['url']}")
    subcats = extract_subcategories(cat["url"])
    category_tree.append({
        "name": cat["name"],
        "url": cat["url"],
        "subcategories": subcats
    })

# -----------------------
# Step 3: Save to MongoDB using CategoryItem
# -----------------------
for cat_data in category_tree:
    try:
        CategoryItem(**cat_data).save()
        logging.info(f" Saved main category: {cat_data['name']}")
    except Exception as e:
        logging.error(f" Error saving category {cat_data['name']}: {e}")

logging.info(" Finished saving all categories to MongoDB.")
