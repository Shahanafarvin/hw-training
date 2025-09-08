import requests
from lxml import html
from urllib.parse import urljoin
import json

base_url = "https://www.next.co.uk"
start_url = "https://www.next.co.uk/women"

response = requests.get(start_url)
print(response.status_code)

html_content = html.fromstring(response.content)

# Category links
category_links = html_content.xpath('//li[@class=" header-16hexny"]/a/@href')

# List of IDs to iterate through (subcategory containers)
ids = [
    "multi-11-teaser-474850-3_item_",
    "multi-11-teaser-479476-3_item_",
    "multi-11-teaser-474318-3_item_",
    "multi-11-teaser-473758-3_item_",
    "multi-11-teaser-478208-3_item_",
    "multi-3-teaser-1013880-2_item_",
    "multi-11-teaser-475374-3_item_",
    "multi-11-teaser-657180-3_item_",
    "multi-11-teaser-480676-3_item_",
    "multi-11-teaser-472530-3_item_",
    "multi-11-teaser-473438-3_item_",
    "multi-3-teaser-286336-3_item_"
]

# Function to get product URLs from a single subcategory page (no pagination)
def get_product_urls(sub_url):
    product_urls = set()
    print(f"Fetching products from: {sub_url}")
    res = requests.get(sub_url)
    tree = html.fromstring(res.content)

    # Product URLs (look for /style/ links)
    links = tree.xpath('//a[@class="MuiCardMedia-root  produc-1mup83m"]/@href')
    for link in links:
        full_link = urljoin(base_url, link)
        product_urls.add(full_link)

    return list(product_urls)


# Final results dictionary
all_data = {}

for link in category_links[1:]:  
    category_url = urljoin(base_url, link)
    category_response = requests.get(category_url)
    category_html = html.fromstring(category_response.content)
    
    print(f"\n\nSubcategories for {category_url}:")
    for id_value in ids:
        subcategory_links = category_html.xpath(f'//div[contains(@id,"{id_value}")]/div/a/@href')
        for sub_link in subcategory_links:
            full_sub_link = urljoin(base_url, sub_link)
            print(f" Subcategory: {full_sub_link}")

            # Get product URLs from this subcategory
            product_urls = get_product_urls(full_sub_link)
            all_data[full_sub_link] = product_urls
            print(f"  Found {len(product_urls)} products")


# Save results as JSON
with open("next_products.json", "w", encoding="utf-8") as f:
    json.dump(all_data, f, indent=4, ensure_ascii=False)

print("\n Data saved to next_products.json")
