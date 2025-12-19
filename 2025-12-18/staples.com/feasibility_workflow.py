import requests
import json
from parsel import Selector

#---------------------------category--------------------------------------------------------------------------------

url = "https://www.staples.com/ele-lpd/api/common/lpdProxy-common/getMenuContent"

headers = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json;charset=UTF-8",
    "origin": "https://www.staples.com",
    'referer': 'https://www.staples.com/',
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
}

cookies = {
    "zipcode": "01701",
    "geocode": "42.298643,-71.465635",
    "ListGridMode": "true"
}

payload = {
    "id": "9f93268c-e044-4971-8458-c81e1ba56caf",
    "routeDetails": {
        "routeType": "sdc",
        "routeId": "sdc",
        "isWhiteLabel": False
    },
    "siteVariables": {
        "tenant": {
            "legacy": 10001,
            "fullName": "StaplesDotCom",
            "shortName": "sdc"
        },
        "channelId": "WEB",
        "siteId": "US",
        "catalogId": "10051",
        "langId": -1,
        "langCd": "en",
        "locale": "en_US",
        "hyphenatedLocale": "en-US",
        "storeId": "10001",
        "currency": "USD",
        "isCOM": True,
        "isCA": False,
        "isSBA": False,
        "assetStoreId": 5051,
        "env": "azureprod",
        "isProd": True,
        "isLoggedIn": False,
        "ctx": {},
        "zipCode": "01701"
    }
}

response = requests.post(
    url,
    headers=headers,
    cookies=cookies,
    json=payload,
    timeout=30
)

print("Status code:", response.status_code)


data = response.json()
category_tree = []
seen = set()  # track duplicates

# root can be dict {"0": {...}} or list [{...}]
roots = data.values() if isinstance(data, dict) else data

for root in roots:
    navigation_flyouts = root.get("navigationFlyouts", [])

    # only second flyout
    if isinstance(navigation_flyouts, list) and len(navigation_flyouts) > 1:
        second_flyout = navigation_flyouts[1]

        for item in second_flyout.get("navigationFlyoutsItems", []):
            label = item.get("ariaLabel")
            url = item.get("destinationURL")
            
            if not label or not url:
                continue  # skip invalid entries

            key = (label, url)
            if key in seen:
                continue  # skip duplicates
            seen.add(key)

            category = {
                "ariaLabel": label,
                "destinationURL": f"https://www.staples.com/{url.lstrip('/')}"
            }

            category_tree.append(category)  #main category extracted
#-------------------------subcategories----------------------------------------

BASE_URL = "https://www.staples.com"
START_URL = "https://www.staples.com/Office-Supplies/cat_SC1" #MAIN CATEGORY URL TO GET SUB LEVELS

response = requests.get(START_URL)
sel = Selector(response.text)

category_tree = []

# Level 1: subcategories
subcategories = sel.xpath("//a[@class='seo-component__seoLink']/@href").getall()

for subcat in subcategories:
    subcat_url = f"{BASE_URL}{subcat}"
    res2 = requests.get(subcat_url)
    sel2 = Selector(res2.text)

    subcat_node = {
        "category_url": subcat_url,
        "children": []
    }

    # Level 2: sub-subcategories (same XPath)
    sub_subcategories = sel2.xpath("//a[@class='seo-component__seoLink']/@href").getall()

    if sub_subcategories:
        for ssub in sub_subcategories:
            ssub_url = f"{BASE_URL}{ssub}"

            subcat_node["children"].append({
                "subcategory_url": ssub_url
            })
    else:
        subcat_node["children"] = []

    category_tree.append(subcat_node)



#--------------------------------crawler-------------------------------------------------------
import requests
import json
import math
from parsel import Selector

BASE_URL = "https://www.staples.com"
START_URL = "https://www.staples.com/Pens/cat_CL110001"

all_products = []
page = 1


# ---- First page (to get total count) ----
res = requests.get(START_URL)
sel = Selector(res.text)

script_text = sel.xpath("//script[@id='__NEXT_DATA__']/text()").get()
data = json.loads(script_text)

search_state = (
    data.get("props", {})
        .get("initialStateOrStore", {})
        .get("searchState", {})
)

total_products = search_state.get("totalCount", 0)
page_size=search_state.get("itemsPerPage",40)
products = search_state.get("productTileData", [])

all_products.extend(products)

total_pages = math.ceil(total_products / page_size)

print(f"Total products: {total_products}")
print(f"Total pages: {total_pages}")

# ---- Remaining pages ----
for page in range(2, total_pages + 1):
    paginated_url = f"{START_URL}?pn={page}"
    res = requests.get(paginated_url)
    sel = Selector(res.text)

    script_text = sel.xpath("//script[@id='__NEXT_DATA__']/text()").get()
    data = json.loads(script_text)

    products = (
        data.get("props", {})
            .get("initialStateOrStore", {})
            .get("searchState", {})
            .get("productTileData", [])
    )

    all_products.extend(products)
    print(f"Fetched page {page} → {len(products)} products")

# ---- Final extraction ----
for product in all_products:
    sku = product.get("compareItemID")
    site_url = product.get("url")
    product_title = product.get("title")
    brand = product.get("brandName")
    category = product.get("baseCatName")
    cost = product.get("price")
    notes = product.get("description")

    # Example output
    # print(sku, site_url, product_title)

print(f"\nTotal collected products: {len(all_products)}")

#TAKE BADGES IF NEEDED?

#------------------------------------findings--------------------------------------------------------
#.category API responses have a dynamic structure, which can lead to parsing errors.
#.Main categories are extracted from APIs, and subcategories are extracted recursively from each category’s HTML response
#  until the final category level.

#Products are available within the scripts of PLP pages, and no parser-based extraction is currently required.
