import requests
import time
from parsel import Selector

#--------------------------category api generation-----------------------
api_url = "https://www.jiomart.com/moonx/rest/v1/homepage/trexcategorydetails?type=1&category=2"
headers = {
    "accept": "*/*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "location_details": '{"city":"Mumbai","state_code":"MH","store_code":{"LOCALSHOPS":{"3P":["3P38SR7XFC60","3PFUIPOCFC01","3PT3LXIHFC05","3P13PK7AFC18","3P38SR7XFC33","3P2G9P4DFC02","3P38SR7XFC67"]},"GROCERIES":{"3P":["groceries_zone_non-essential_services","general_zone","groceries_zone_essential_services"],"1P":["T9V1"]},"FASHION":{"3P":["fashion_zone","general_zone"],"1P":["S535","R975","S402","SURR","R300","SLI1","V017","SB41","TG1K","SLE4","SLTP","T4QF","SANR","S0XN","SANS","SL7Q","SZBL","SANQ","Y524","S4LI","SH09","V027","SJ14","V012"]},"JEWELLERY":{"1P":["VLOR"]},"PREMIUMFRUITS":{"1P":["S575"]},"BOOKS":{"3P":["general_zone"],"1P":["SANR","SANS","SURR","SANQ","S4LI"]},"FURNITURE":{"3P":["general_zone"],"1P":["440","254","60","270"]},"SPORTSTOYSLUGGAGE":{"3P":["general_zone"],"1P":["SANR","SANS","SURR","SANQ","S4LI"]},"HOMEIMPROVEMENT":{"3P":["general_zone"],"1P":["SANR","SANS","SURR","SANQ","S4LI"]},"HOMEANDKITCHEN":{"3P":["general_zone"],"1P":["SANR","SANS","SURR","SANQ","S4LI"]},"CRAFTSOFINDIA":{"3P":["general_zone"],"1P":["SANR","SANS","SURR","SANQ","S4LI"]},"WELLNESS":{"1P":["SF11","SF40","SX9A"]},"ELECTRONICS":{"3P":["electronics_zone","general_zone"],"1P":["SACU","R696","SE40","S0BN","R080","SK1M","Y344","SJ93","R396","S573","SLTY","V014","SLKO"]}},"region_code":{"BOOKS":["PANINDIABOOKS"],"CRAFTSOFINDIA":["PANINDIACRAFT"],"ELECTRONICS":["PANINDIADIGITAL"],"FASHION":["PANINDIAFASHION"],"FURNITURE":["PANINDIAFURNITURE"],"GROCERIES":["TXCF","PANINDIAGROCERIES"],"HOMEANDKITCHEN":["PANINDIAHOMEANDKITCHEN"],"HOMEIMPROVEMENT":["PANINDIAHOMEIMPROVEMENT"],"JEWELLERY":["PANINDIAJEWEL"],"LOCALSHOPS":["PANINDIALOCALSHOPS"],"PREMIUMFRUITS":["S575"],"SPORTSTOYSLUGGAGE":["PANINDIASTL"],"WELLNESS":["PANINDIAWELLNESS"]},"vertical_code":["LOCALSHOPS","GROCERIES","FASHION","JEWELLERY","PREMIUMFRUITS","BOOKS","FURNITURE","SPORTSTOYSLUGGAGE","HOMEIMPROVEMENT","HOMEANDKITCHEN","CRAFTSOFINDIA","WELLNESS","ELECTRONICS"]}',
    "pin": "400008",
    "pragma": "no-cache",
    "referer": "https://www.jiomart.com/all-category",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
}
response = requests.get(api_url, headers=headers)
data = response.json()
categories = data.get("resultData", [])
tree = {}

cat_name = categories[0].get("name")
cat_id = categories[0].get("id")
tree[cat_name] = {"id": cat_id, "sub_categories": {}}

for sub in categories[0].get("sub_categories", []):
    sub_name = sub.get("name")
    sub_id = sub.get("id")
    tree[cat_name]["sub_categories"][sub_name] = {"id": sub_id, "sub_categories": {}}

    for sub_sub in sub.get("sub_categories", []):
        sub_sub_name = sub_sub.get("name")
        sub_sub_id = sub_sub.get("id")
        tree[cat_name]["sub_categories"][sub_name]["sub_categories"][sub_sub_name] = {"id": sub_sub_id}


#-----------------------------crawler-----------------------------------------------------
API_URL = "https://www.jiomart.com/trex/search"
headers = {
    "accept": "*/*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "origin": "https://www.jiomart.com",
    "pragma": "no-cache",
    "referer": "https://www.jiomart.com/c/groceries",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
}

cookies = {
    "nms_mgo_city": "Mumbai",
    "nms_mgo_state_code": "MH",
    "nms_mgo_pincode": "400008",
}
all_products = []
def walk(tree, parent_name=""):
    global total_count

    for name, details in tree.items():
        sub = details.get("sub_categories", None)
        if sub:
            walk(sub, parent_name + " > " + name if parent_name else name)
        else:
            cat_id = details["id"]
            full_path = (parent_name + " > " + name).strip(" >")
            print(f"Category: {full_path} (ID: {cat_id})")

            payload = {
                "pageSize": 50,
                "facetSpecs": [
                    {"facetKey": {"key": "brands"}, "limit": 500, "excludedFilterKeys": ["brands"]},
                    {"facetKey": {"key": "categories"}, "limit": 500, "excludedFilterKeys": ["categories"]},
                    {"facetKey": {"key": "attributes.category_level_4"}, "limit": 500, "excludedFilterKeys": ["attributes.category_level_4"]},
                    {"facetKey": {"key": "attributes.category_level_1"}, "excludedFilterKeys": ["attributes.category_level_4"]},
                    {"facetKey": {"key": "attributes.avg_selling_price", "return_min_max": True,
                                  "intervals": [{"minimum": 0.1, "maximum": 100000000}]}},
                    {"facetKey": {"key": "attributes.avg_discount_pct", "return_min_max": True,
                                  "intervals": [{"minimum": 0, "maximum": 99}]}}
                ],
                "variantRollupKeys": ["variantId"],
                "branch": "projects/sr-project-jiomart-jfront-prod/locations/global/catalogs/default_catalog/branches/0",
                "pageCategories": [str(cat_id)],
                "userInfo": {"userId": None},
                "orderBy": "attributes.popularity desc",
                "filter": (
                    f'attributes.status:ANY("active") AND attributes.category_ids:ANY("{cat_id}") AND '
                    '(attributes.available_regions:ANY("TXCF", "PANINDIAGROCERIES")) AND '
                    '(attributes.inv_stores_1p:ANY("ALL", "T9V1") OR '
                    'attributes.inv_stores_3p:ANY("ALL", "groceries_zone_non-essential_services", '
                    '"general_zone", "groceries_zone_essential_services"))'
                ),
                "visitorId": "anonymous-3dea4a71-ffac-4226-97e4-0d853392d5e5",
            }

            page = 1
            while True:
            
                r = requests.post(API_URL, headers=headers, cookies=cookies, json=payload, timeout=20)
                data = r.json()

                results = data.get("results", [])
                for product in results:
                    variant = product.get("product", {}).get("variants", [{}])[0]
                    product_info = {
                        "unique_id": variant.get("id", ""),
                        "brand": (variant.get("brands", [""])[0] if variant.get("brands") else ""),
                        "title": variant.get("title", ""),
                        "pdp_url": variant.get("uri", ""),
                        "images": variant.get("images", []),
                        "category_path": product.get("product", {}).get("categories", []),
                        "alternate_ids": variant.get("attributes", {}).get("alternate_product_code").get("text",""),
                    }
                    all_products.append(product_info)

                next_token = data.get("nextPageToken")
                if next_token:
                    payload["pageToken"] = next_token
                    time.sleep(0.5)
                else:
                    break

walk(tree)  #function call to start walking the tree

#-----------------------parser-----------------------------------------------------------------
url = "https://www.jiomart.com/p/groceries/kurkure-combo-pack-99-g-pack-of-3/590033333"


# Fetch the page
response = requests.get(url)
response.raise_for_status()

sel = Selector(text=response.text)

# Extract using XPath
title = sel.xpath("//div[@id='pdp_product_name']/text()").get()
description = sel.xpath('//div[@id="pdp_description"]//text()').getall()
info=sel.xpath('//div[@id="pdp_product_information"]//text()').getall()#need to clean and extract as dictionary

#--------------------------price extraction----------------------------------------------
url = "https://www.jiomart.com/catalog/productdetails/get/590033333"  #url need to be generated dynamically using product id

headers = {
    "accept": "application/json, text/javascript, */*; q=0.01",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "pin": "400008",
    "pragma": "no-cache",
    "referer": "https://www.jiomart.com/p/groceries/kurkure-combo-pack-99-g-pack-of-3/590033333",
    "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
}

cookies = {
    "nms_mgo_city": "Mumbai",
    "nms_mgo_state_code": "MH",
    "nms_mgo_pincode": "400008",
}

response = requests.get(url, headers=headers, cookies=cookies)
data = response.json()
product_data = data.get("data", {})

availability_status = product_data.get("availability_status", "")
discount_pct = product_data.get("discount_pct", "")
mrp = product_data.get("mrp", "")
selling_price = product_data.get("selling_price", "")

product_info = {
    "availability_status": availability_status,
    "discount_pct": discount_pct,
    "mrp": mrp,
    "selling_price": selling_price
}

#------------------------review extraction----------------------------------------------
url = "https://reviews-ratings.jio.com/customer/op/v1/review/product-statistics/490709191"#url need to be generated dynamically using alternate id
headers = {
    "accept": "application/json",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "access-control-allow-origin": "*",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "jwt-token": "null",
    "origin": "https://www.jiomart.com",
    "pragma": "no-cache",
    "referer": "https://www.jiomart.com/",
    "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "userid": "0",
    "vertical": "jiomart",
}
response = requests.get(url, headers=headers)
data = response.json()
# Extract required fields
average_rating = data.get("data",{}).get("averageRating", "")
ratings_count = data.get("data",{}).get("ratingsCount", "")

review_info = {
    "averageRating": average_rating,
    "ratingsCount": ratings_count
}

#-------------------------findings------------------------------------------------
# URLs cannot be extracted from HTML; an API was found for crawling.

# Pagination uses a nextPage token, which must be generated dynamically each time.

# Category API URLs need to be generated.

# Parsing can be done through HTML, but additional API requests are required for price and review details.

# The crawler is omitting 502 and 503 errors, and rate limiting has been detected
#curl_cffi with browser impersonation (impersonate="chrome120") and a retry-with-random-delay mechanism to handle 502 and 503 errors, 
# effectively bypassing rate limits and TLS fingerprinting blocks.
