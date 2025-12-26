import requests
from parsel import Selector
import json
#----------------------------category-----------------------------------------------------------
url="https://www.lorespresso.com/en_gb"

response = requests.get(url)
print(response.status_code)


sel = Selector(text=response.text)
categories=sel.xpath("//a[@class='MuiTypography-root MuiTypography-inherit MuiLink-root MuiLink-underlineAlways mui-style-1wlgmvd']/@href").getall()
print(categories)

#------------------------------crawler----------------------------------------------------------
categories = [
    "capsules",
    "Coffee machine",
    "Accessories",
    "Instant Coffee",
    "Coffee Beans"
]

# convert to slugs
def to_slug(name):
    return name.lower().replace("'", "").replace(" ", "-")

category_slugs = [to_slug(cat) for cat in categories]
print(category_slugs)



headers = {
    "sec-ch-ua-platform": '"Linux"',
    "Referer": "https://www.lorespresso.com/en_gb/capsules",
    "purpose": "prefetch",
    "x-middleware-prefetch": "1",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "newrelic": "eyJ2IjpbMCwxXSwiZCI6eyJ0eSI6IkJyb3dzZXIiLCJhYyI6IjYyODQwMTAiLCJhcCI6IjE1ODkwNDU5NzgiLCJpZCI6ImMyOWMzZDgyOTNmNGNlMTgiLCJ0ciI6ImEzYTBhM2E0MWY2ZjVhNTViMzA2Y2RkMDMxYWYzNDVhIiwidGkiOjE3NjY0ODIxMTY5NDl9fQ==",
    "sec-ch-ua-mobile": "?0",
    "request-id": "|56746b154b7a4b69b346477e6c743a7c.9be46b34e9c6468e",
    "x-nextjs-data": "1",
    "traceparent": "00-a3a0a3a41f6f5a55b306cdd031af345a-c29c3d8293f4ce18-01",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "tracestate": "6284010@nr=0-1-6284010-1589045978-c29c3d8293f4ce18----1766482116949"
}

all_products = []


all_products = []

for category in category_slugs:
    url = f"https://www.lorespresso.com/_next/data/liEcZFYMRVmiiJWDSN8Yr/en_gb/{category}.json?url={category}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Scraping category: {category}, URL: {url}")
        
        # Extract products safely
        products_data = data.get("pageProps", {}).get("products", {})
        if "product_ranges" in products_data:
            products_categories = products_data["product_ranges"]
        else:
            products_categories = [products_data]  # wrap in list for uniform iteration
        
        for pcat in products_categories:
            # Some categories use nested structure, some are flat
            products = (
                pcat.get("category", {}).get("products", {}).get("items", []) or
                pcat.get("items", [])
            )
            
            for product in products:
                product_info = {
                    "name": product.get("name"),
                    "sku": product.get("sku"),
                    "url": f"https://www.lorespresso.com/en_gb/p/{product.get('url_key')}",
                    "rating": product.get("rating_summary"),
                    "review": product.get("review_count"),
                    "price_details": product.get("price_range")
                }
                print(product_info)
                all_products.append(product_info)
        
    else: 
        print(f"Failed to retrieve data for category: {category}, Status Code: {response.status_code}")


#----------------------------------parser-------------------------------------------------------------------


url="https://www.lorespresso.com/en_gb/p/milk-frother-lor-uk"
response=requests.get(url)
print(response.status_code)

sel=Selector(text=response.text)
description=sel.xpath("//div[@data-testid='product-description']//p/text()").getall()
print(description)

bullets=sel.xpath("//ul[@class='MuiList-root MuiList-padding brand-lor mui-style-1t9ifb2']/li//text()").getall()
print(bullets)

# Extract JSON-LD scripts
json_ld_scripts = sel.xpath('//script[@type="application/ld+json"]/text()').getall()

product_data = None
breadcrumb_data = None

for script in json_ld_scripts:
    try:
        data = json.loads(script.strip())

        if isinstance(data, dict):
            if data.get("@type") == "Product":
                product_data = data

            elif data.get("@type") == "BreadcrumbList":
                breadcrumb_data = data

    except json.JSONDecodeError:
        continue

breadcrumb_items = breadcrumb_data.get("itemListElement", [])

# Sort by position just to be safe
breadcrumb_items = sorted(
    breadcrumb_items,
    key=lambda x: x.get("position", 0)
)

breadcrumbs = " > ".join(
    item.get("name", "").strip()
    for item in breadcrumb_items
    if item.get("name")
)

product = {
    "name": product_data.get("name"),
    "sku": product_data.get("sku"),
    "category": product_data.get("category"),
    "images": product_data.get("image", []),

    "price_currency": product_data.get("offers", {}).get("priceCurrency"),
    "low_price": product_data.get("offers", {}).get("lowPrice"),
    "high_price": product_data.get("offers", {}).get("highPrice"),

    "rating_value": product_data.get("aggregateRating", {}).get("ratingValue"),
    "review_count": product_data.get("aggregateRating", {}).get("reviewCount"),

    "breadcrumbs": breadcrumbs,
}

print(json.dumps(product, indent=2))



#-----------------------------------findings---------------------------------------------------------------

#1. Categories are extracted from the base HTML response, and
 #the last part of the URL is split and used to generate APIs for product extraction.