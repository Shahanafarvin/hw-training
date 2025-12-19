import requests
import json

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
START_URL = "https://www.staples.com/Office-Supplies/cat_SC1"

response = requests.get(START_URL)
sel = Selector(response.text)

category_tree = []

# Level 1: main subcategories
subcategories = sel.xpath("//a[@class='seo-component__seoLink']/@href").getall()

for subcat in subcategories:
    subcat_url = f"{BASE_URL}{subcat}"
    response2 = requests.get(subcat_url)
    sel2 = Selector(response2.text)

    subcat_node = {
        "url": subcat_url,
        "children": []
    }

    # Level 2: sub-subcategories
    subsubcategories = sel2.xpath("//a[@class='seo-component__seoLink']/@href").getall()

    if subsubcategories:
        for ssub in subsubcategories:
            ssub_url = f"{BASE_URL}{ssub}"
            response3 = requests.get(ssub_url)
            sel3 = Selector(response3.text)

            ssub_node = {
                "url": ssub_url,
                "end_level": []
            }

            # Level 3: end-level categories (carousel items)
            end_level = sel3.xpath(
                "//div[starts-with(@id,'offset-carousel-item-')]//a/@href"
            ).getall()

            ssub_node["end_level"] = [
                f"{BASE_URL}{e}" for e in end_level
            ]

            subcat_node["children"].append(ssub_node)
    else:
        # If no sub-subcategories, directly extract end-level
        end_level = sel2.xpath(
            "//div[starts-with(@id,'offset-carousel-item-')]//a/@href"
        ).getall()

        subcat_node["end_level"] = [
            f"{BASE_URL}{e}" for e in end_level
        ]

    category_tree.append(subcat_node)

#--------------------------------crawler-------------------------------------------------------
from curl_cffi import requests
import json

url = "https://www.staples.com/searchux/common/api/v1/All-In-One-Printers/cat_CL167883/8v6qy?isVF=true"

headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "referer": "https://www.staples.com/Ballpoint-pens/cat_CL110001/87vsv?isVF=true",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty"
}

cookies = {
    "zipcode": "01701",
    "geocode": "42.298643,-71.465635",
    "ListGridMode": "true"
}

response = requests.get(url, headers=headers, cookies=cookies, impersonate="chrome")

print(response.status_code)

data=response.json()
products=data.get("searchState",{}).get("productTileData")
print(len(products))
for product in products:
    brand=product.get("brandName")
    product_title=product.get("title")
    sku=product.get("compareItemID")
    category=product.get("hierarchy",{}).get("category").get("name")
    site_url=f"https://www.staples.com{product.get('url')}"
    cost=product.get("price")
    notes=product.get("description")
    badge_details = product.get("badgeDetails", {})

    # badges = []
    # if badge_details.get("productBadge"):
    #     badges.append(badge_details["productBadge"])
    # if badge_details.get("pricingBadge"):
    #     badges.append(badge_details["pricingBadge"])#checking if best seller available
    # product_url=site_url
    # product_cost_brand=cost

   

#------------------------------------findings--------------------------------------------------------
#.category API responses have a dynamic structure, which can lead to parsing errors.
#.Main categories are extracted from APIs, and subcategories are extracted recursively from each category’s HTML response
#  until the final category level.
#.Products are extracted directly from each PLP API response, and no parser-based extraction is currently required.

#Products are available within the scripts of PLP pages, and selecting this option may require a parser