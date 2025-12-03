from curl_cffi import requests
from parsel import Selector
import json
from datetime import datetime
import re

#-------------------------category extraction-------------------------------------------------------------------
url = "https://www.maxfashion.com/ae/en/"

res = requests.get(
    url,
    impersonate="chrome",
    timeout=60
)

sel = Selector(res.text)

category_tree = []

categories = sel.xpath('//div[contains(@class,"jss101 departments")]')

for category in categories:
    category_name = category.xpath('./a//text()').get()
    category_url = f"https://www.maxfashion.com{category.xpath('./a/@href').get()}"

    category_node = {
        "name": category_name,
        "url": category_url,
        "subcategories": []
    }

    subcategories = category.xpath('.//div[contains(@class,"jss117 category")]')

    for subcat in subcategories:
        subcategory_name = subcat.xpath('.//a//text()').get()
        subcategory_url = f"https://www.maxfashion.com{subcat.xpath('.//a/@href').get()}"

        subcategory_node = {
            "name": subcategory_name,
            "url": subcategory_url,
            "subsubcategories": []
        }

        subsubcats = subcat.xpath('.//div[@class="jss133"]')

        for subsub in subsubcats:
            subsubcategory_name = subsub.xpath('./a/text()').get()
            subsubcategory_url = f"https://www.maxfashion.com{subsub.xpath('./a/@href').get()}"

            subsubcategory_node = {
                "name": subsubcategory_name,
                "url": subsubcategory_url
            }

            subcategory_node["subsubcategories"].append(subsubcategory_node)

        category_node["subcategories"].append(subcategory_node)

    category_tree.append(category_node)

#-----------------------------------------crawler--------------------------------------------------------
base = "https://www.maxfashion.com"

for cat in category_tree:
    cat_name = cat.get("name")

    for subcat in cat.get("subcategories", []):
        subcat_name = subcat.get("name")

        for final in subcat.get("subsubcategories", []):
            final_name = final.get("name")
            final_url = final.get("url")

            # First request only once
            res = requests.get(final_url, impersonate="chrome", timeout=60)
            sel = Selector(text=res.text)

            # Extract last page number
            last_page = sel.xpath('//ul[contains(@class,"jss")]/li[last()-1]//text()').get()
            try:
                last_page = int(last_page)
            except:
                last_page = 1  

            # --- PAGE 1 (use existing HTML, no new request) ---
            page_html = sel  # reuse selector

            # Extract product URLs for page 1
            products = page_html.xpath('//a[contains(@id,"prodItemImgLink")]/@href').getall()
            products = [base + p for p in products]

            # Now loop for page 2 onwards
            for page in range(2, last_page + 1):

                if "?" in final_url:
                    page_url = final_url + f"&p={page}"
                else:
                    page_url = final_url + f"?p={page}"

                res = requests.get(page_url, impersonate="chrome", timeout=60)
                sel = Selector(text=res.text)

                more_products = sel.xpath('//a[contains(@id,"prodItemImgLink")]/@href').getall()
                more_products = [base + p for p in more_products]

                products.extend(more_products)


#-----------------------------parser.py---------------------------------------------------------
# API endpoint
url = 'https://www.maxfashion.com/api/catalog-browse/products/sku'

# Query parameters
params = {
    'productSkus': 'C25WCTFEKT140KNAVYDARK' #change sku for each product which is last part of url
}

# Headers
headers = {
    'accept': '*/*',
    'accept-language': 'en-US, en-US',
    'cache-control': 'no-cache',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
    'x-context-request': '{"applicationId":"mx-ae","tenantId":"5DF1363059675161A85F576D"}',
    'x-lmg-context-request': '{"lang":"en","platform":"Desktop"}',
    'x-price-context': '{"locale":"en","currency":"AED"}'
}

# Make the request
response = requests.get(url,impersonate="chrome", params=params, headers=headers)

# Print JSON response
if response.status_code == 200:
   
    data = response.json()
    product=data.get('products', [])[0]  # Get the first product
    id=product.get('id')
    name=product.get('name')
    details={}
    attributes=product.get('attributes', {})
    #print(attributes)
    for key, attr in attributes.items():
                if isinstance(attr, dict):
                    name = attr.get('nameLabel', key)
                    value = attr.get('value', 'N/A')
                if name not in ["Care Instructions"]:
                    details[name] = value 

    regular_price = product.get('priceInfo', {}).get('price', {}).get('amount',"")
    image_url = product.get('primaryAsset',{}).get('url',"")
    description = product.get('description', '')
    currency = product.get('priceInfo', {}).get('price', {}).get('currency', 'AED')
    breadcrumbs_list = product.get('breadcrumbs', [])
    breadcrumbs=" > ".join([crumb.get('label', '') for crumb in breadcrumbs_list])
    extracted_date=datetime.now().strftime("%Y-%m-%d")
#gender can be generated from breadcrumbs

#-------------------------------------extra html request for selling price,size,color--------------------------------
url = "https://www.maxfashion.com/ae/en/buy-plain-zip-through-hoodie-with-kangaroo-pockets/p/C24MBSBCKZTH101NAVYDARK" #product url
response = requests.get(url, impersonate="chrome")
selector = Selector(text=response.text)

# Extract JSON data from the script tag
product_json = selector.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
#selling price
match = re.search(r'"salePrice"\s*:\s*\{.*?"amount":\s*([0-9]+)', product_json, re.S)
if match:
    sale_price = match.group(1)
#size
pattern = r'"attributeName"\s*:\s*"Size".*?"allowedValues"\s*:\s*\[(.*?)\]'
block = re.search(pattern, product_json, re.S)
sizes = []
if block:
    sizes = re.findall(r'"value"\s*:\s*"([^"]+)"', block.group(1))
size = sorted(set(sizes))
#color
value_to_find = "C24MBSBCKZTH101NAVYDARK"  #last part of url
pattern = (
    r'"label"\s*:\s*"([^"]+)"\s*,\s*'
    r'"value"\s*:\s*"' + re.escape(value_to_find) + r'"'
)
match = re.search(pattern, product_json)
if match:
    color = match.group(1)



#------------------------------findings------------------------------------------------

#1. The request response was repeatedly returning 403, and this issue was handled successfully using curl_cffi.

#2. PLP page extraction works through normal HTML parsing, but the PDP pages are heavily JavaScript-rendered with no usable data in visible
# HTML tags. Most details are found inside script tags, and some additional fields are available only through API responses.

#3. Request depth had to be increased to 2 levels because the API provides only partial data; additional fields like size, color, a
# nd sale price are available only inside script tags. Extracting them using regex can be complicated and may lead to occasional mismatches.

#4. The gender field can only be inferred from breadcrumbs, so missing or inconsistent values are possible.