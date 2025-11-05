import requests
from parsel import Selector
import json

# -------------------------
# category url generation
# -------------------------

def extract_subcategories(url, depth=1):
    """
    Recursively extract all nested subcategories from the given URL.
    Stops when no further subcategories are found.
    """
    resp= requests.get(url, timeout=30)
    sel = Selector(resp.text)
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

        # Recursive call for nested subcategories
        sub_subcats = extract_subcategories(href, depth + 1)

        subcategories.append({
            "name": sub_name,
            "url": href,
            "subcategories": sub_subcats
        })
        
    return subcategories

BASE_URL = "https://www.mrosupply.com"
response = requests.get(BASE_URL)
sel = Selector(response.text)

main_categories = []
for cat in sel.xpath('//li[contains(@class,"o-categories-list--item")]/a'):
    url = cat.xpath('./@href').get()
    if url:
        url = url.strip()
        full_href = BASE_URL.rstrip("/") + url
        name = url.replace("/", "").replace("-", " ").strip().title()
        main_categories.append({"name": name, "url": full_href})

category_tree = []
for cat in main_categories:
    print(f"\nProcessing main category: {cat['name']} → {cat['url']}")
    subcats = extract_subcategories(cat["url"])
    category_tree.append({
        "name": cat["name"],
        "url": cat["url"],
        "subcategories": subcats
    })

#-------------------------
# crawler to extract product urls
#-------------------------

for main_cat in category_tree:
    stack = [main_cat]
    while stack:
        node = stack.pop()

        # Traverse subcategories if present
        if "subcategories" in node and node["subcategories"]:
            stack.extend(node["subcategories"])
        else:
            print(f"\nExtracting products from leaf: {node['name']}")
            products = []
            next_page_url = node["url"]

            # Paginate until next page link disappears
            while next_page_url:
                
                response = requests.get(next_page_url)
                sel = Selector(response.text)

                # Extract product URLs
                for p in sel.xpath('//a[@class="m-catalogue-product-title js-product-link"]/@href').getall():
                    products.append(BASE_URL + p.strip())

                # Find next page
                next_link = sel.xpath('//a[@aria-label="Go to next page"]/@href').get()
                if next_link:
                    next_page_url = BASE_URL + next_link.strip()
                else:
                    next_page_url = None

            node["products"] = products
           
#-------------------------
#parser to extract product details
#-------------------------
products_data = []

# Traverse all categories and scrape products
for main_cat in category_tree:
    stack = [main_cat]
    while stack:
        node = stack.pop()

        # Traverse subcategories if they exist
        if "subcategories" in node and node["subcategories"]:
            stack.extend(node["subcategories"])
            continue

        # If it's a leaf node with products
        if "products" in node and node["products"]:
            
            for url in node["products"]:
                try:
                    r = requests.get(url)
                    r.raise_for_status()
                    sel = Selector(r.text)
                    data = {}

                    # Extract JSON-LD script
                    json_text = sel.xpath('//script[@type="application/ld+json"]/text()').get()
                    if json_text:
                        try:
                            jd = json.loads(json_text)
                            data["Item Name"] = jd.get("name")
                            data["category"] = jd.get("category")

                            # Brand
                            if jd.get("brand"):
                                data["Brand Name"] = jd["brand"].get("name")

                            # Offers
                            offers = jd.get("offers")
                            if isinstance(offers, list):
                                offer = offers[0]
                            else:
                                offer = offers

                            if offer:
                                data["Price"] = offer.get("price")
                                if offer.get("availability"):
                                    data["Availability"] = offer.get("availability").split("/")[-1]
                                if offer.get("seller"):
                                    data["Manufacture name"] = offer["seller"].get("name")
                                    data["Vendor/Seller Part Number"] = offer.get("sku")
                                data["Manufacturer Part Number"] = offer.get("mpn")

                            data["QTY Per UOI"] = jd.get("weight")

                        except json.JSONDecodeError:
                            pass

                    # Company and URL
                    data["Company Name"] = "MRO Supply"
                    data["URL"] = url

                    # Extract description table
                    description = {}
                    for row in sel.xpath('//table[@class="description-table"]//tr'):
                        key = row.xpath('.//th/text()').get()
                        val = row.xpath('.//td/text()').get()
                        if key and val:
                            description[key.strip()] = val.strip()

                    data["Full Product Description"] = ", ".join(f"{k}: {v}" for k, v in description.items())
                    data["model number"] = data.get("Manufacturer Part Number")

                    products_data.append(data)
                    print(f" Scraped: {data.get('Item Name')}")

                except Exception as e:
                    print(f"Failed: {url} → {e}")

#-------------------------
# Findings
#------------------------
# category URLs must be extracted recursively to obtain all end-level categories.




