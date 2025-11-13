import requests
import json
from parsel import Selector
import re

#-----------------category api url generation--------------
url = "https://www.matalanme.com/ae_en"#base url


response = requests.get(url)
sel= Selector(response.text)
print(response.status_code)
category=sel.xpath("//li[@class='navMenu_nav_item__sX98P navMenu_dropdown__7q_K8']/a/@href").getall()


url="https://www.matalanme.com/ae_en/category/womens"#category url
response = requests.get(url)
sel= Selector(response.text)
print(response.status_code)
sub_category=sel.xpath("//a[@class='categoryTypeWidget_tab_content_link__x7IFN d-flex flex-column align-items-center']/@href").getall()

url="https://www.matalanme.com/ae_en/women/tops" #sub category url
response = requests.get(url)
sel = Selector(response.text)

# Select the <script> tag that contains "categoryData"
script_text = sel.xpath('//script[contains(text(),"categoryData")]/text()').get()
if script_text:
    # Normalize string: remove newlines and extra spaces
    script_text = script_text.replace("\n", "").replace("\r", "").replace(r'\"', '"').strip()
    
    # Regex to extract UID
    uid_match = re.search(r'"uid"\s*:\s*"([A-Za-z0-9]+)"', script_text)
    
    if uid_match:
        uid = uid_match.group(1)  #collected uids here to generate category api urls

#------------------------crawler-----------------------------------------

url = "https://api.bfab.com/graphql?product_version=1533"

# Headers (from your curl)
headers = {
    "accept": "*/*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "origin": "https://www.matalanme.com",
    "pragma": "no-cache",
    "referer": "https://www.matalanme.com/",
    "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "source": "matalan_city_centre_deira",
    "store": "matalan_ae_en",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "website": "matalan",
}

# GraphQL query string (compact version)
query = """
query GetProductList($filter: ProductAttributeFilterInput, $pageSize: Int, $currentPage: Int, $sort: ProductAttributeSortInput) {
  products(filter: $filter, pageSize: $pageSize, currentPage: $currentPage, sort: $sort) {
    page_info { current_page total_pages }
    items { id sku name url_key brand_name stock_status is_new thumbnail { url } }
  }
}
"""

# GraphQL variables (using your extracted UID)
variables = {
    "filter": {"category_uid": {"in": ["MTcz"]}},#this uid is collected in above step
    "pageSize": 40,
    "currentPage": 1,
    "sort": {}
}

all_items = []

# Step 1: Get first page to find total_pages
response = requests.post(url, headers=headers, json={"query": query, "variables": variables})
data = response.json()
total_pages = data["data"]["products"]["page_info"]["total_pages"]
# Step 2: Loop through all pages
for page in range(1, total_pages + 1):
    variables["currentPage"] = page
    resp = requests.post(url, headers=headers, json={"query": query, "variables": variables})
    page_data = resp.json()
    
    items = page_data.get("data", {}).get("products", {}).get("items", [])
    for item in items:
       # print(item)
        url_info=item.get("url_key")
        availability=item.get("stock_status")
        brand=item.get("brand_name")
        id=item.get("id")
        name=item.get("name")
        price=item.get("price_range").get("minimum_price").get("final_price")
        price_before_discount=item.get("price_range").get("minimum_price").get("regular_price")
        labeling=item.get("product_label")
        all_items.append(url_info)
        print(url_info)
    
#-------------------------------parser-----------------------------------------
url="https://www.matalanme.com/ae_en/light-sequin-yarn-jumper-p-f27602800001" #generated product url from url_info collected in plp crawler
res=requests.get(url)
sel=Selector(res.text)
script_text = sel.xpath('//script[contains(text(),"Specifications")]/text()').get()

text=f'''{script_text}'''
# Step 1: Extract JSON inside self.__next_f.push([...])
match = re.search(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', text)
if not match:
    raise ValueError("No JSON content found in script")

json_str = match.group(1)
# Step 2: Decode escaped quotes
json_str = json_str.encode('utf-8').decode('unicode_escape')

# Step 3: Parse JSON
data = json.loads(json_str)

# Step 4: Extract sections
specifications = {}
description = ""

for section in data:
    title = section.get("title")
    if title == "Specifications":
        for child in section.get("children", []):
            specifications[child["label"]] = child["value"]
    elif title == "Description":
        description = section.get("value", "").strip()

#-----------------extra requests for size and color--------------------------------
url = "https://api.bfab.com/graphql"
params = {
    "product_version": "1534",
    "query": """
        query GetProductVarientOptions($url_key: String!) {
          products(filter: {url_key: {eq: $url_key}}) {
            items {
              selected_variant_options(url_key: $url_key) {
                attribute_id
                value_index
                label
                code
                __typename
              }
              __typename
            }
            __typename
          }
        }
    """,
    "operationName": "GetProductVarientOptions",
    "variables": json.dumps({"url_key": "light-sequin-yarn-jumper-p-f27602800001"})#url key url_info collected for each product
}

headers = {
    "accept": "*/*",
    "content-type": "application/json",
    "origin": "https://www.matalanme.com",
    "referer": "https://www.matalanme.com/",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "store": "matalan_ae_en"
}

response = requests.get(url, params=params, headers=headers)
data = response.json()

# Extract size and color
item = data.get("data", {}).get("products", {}).get("items", [])[0]
options = item.get("selected_variant_options", []) if item else []

size = None
color = None
for opt in options:
    if opt.get("code") == "size":
        size = opt.get("label")
    elif opt.get("code") == "color":
        color = opt.get("label")

#-----------------------findings-------------------
#1. The PLP page has infinite scrolling, so using API calls is more efficient. However, generating category API URLs is complex as it requires additional HTML requests.

#2.  Extra API requests are needed to extract size and color details.

#3. Breadcrumbs need to be generated manually.