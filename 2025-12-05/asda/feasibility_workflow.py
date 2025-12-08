from curl_cffi import requests
import json
from parsel import Selector

#-----------------------------------------------------category tree-----------------------------------------------

BASE_URL = "https://ghs-mm.asda.com/static"

# Headers for requests
common_headers = {
    "accept": "*/*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "origin": "https://www.asda.com",
    "priority": "u=1, i",
    "referer": "https://www.asda.com/",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
}

# Fetch main JSON
url = f"{BASE_URL}/4565.json"
response = requests.get(url, headers=common_headers, impersonate="chrome")
print("Main response:", response.status_code)
data = response.json()

# Extract categories 3, 4, 7
categories = [data[3], data[4], data[7]] #feash and frozen categoruies only

# List to store full category tree
category_tree = []

for cat in categories:
    cat_id = cat.get("id")
    cat_name = cat.get("name")
    cat_url = cat.get("url")

    cat_dict = {
        "id": cat_id,
        "name": cat_name,
        "url": cat_url,
        "subcategories": []
    }

    subcategories = cat.get("depts", [])

    for subcat in subcategories:
        depts = subcat.get("depts")
        sub_id = subcat.get("id")
        sub_name = subcat.get("name")
        sub_url = subcat.get("url")

        sub_dict = {
            "id": sub_id,
            "name": sub_name,
            "url": sub_url,
            "sub_subcategories": []
        }

        # Build URL for sub-sub categories
        if depts:
            next_json_url = f"{BASE_URL}/{depts}.json"

            sub_response = requests.get(next_json_url, headers=common_headers, impersonate="chrome")
            sub_data = sub_response.json()

            for sub_sub in sub_data:
                sub_sub_id = sub_sub.get("id")
                sub_sub_name = sub_sub.get("name")
                sub_sub_url = sub_sub.get("url")
                
                sub_sub_dict = {
                    "id": sub_sub_id,
                    "name": sub_sub_name,
                    "url": sub_sub_url,
                    "sub_subcategories": []
                }

                # Handle next level depts if any
                depts_next = sub_sub.get("depts", [])
                for dept in depts_next:
                    ssub_sub_id = dept.get("id")
                    ssub_sub_name = dept.get("name")
                    ssub_sub_url = dept.get("url")
                    
                    sub_sub_dict["sub_subcategories"].append({
                        "id": ssub_sub_id,
                        "name": ssub_sub_name,
                        "url": ssub_sub_url
                    })

                sub_dict["sub_subcategories"].append(sub_sub_dict)

        cat_dict["subcategories"].append(sub_dict)

    category_tree.append(cat_dict)

#-----------------------------------Crawler--------------------------------------------------------

from curl_cffi import requests
import json
import time

# ---------------------------
# Load category tree
# ---------------------------
with open("asda_category_tree.json", "r", encoding="utf-8") as f:
    category_tree = json.load(f)

# Headers for Algolia request
headers = {
    'Accept': '*/*',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
    'Origin': 'https://www.asda.com',
    'Referer': 'https://www.asda.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'content-type': 'application/x-www-form-urlencoded',
    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'x-algolia-api-key': '03e4272048dd17f771da37b57ff8a75e',
    'x-algolia-application-id': '8I6WSKCCNV',
}

# Output file
output_file = "asda_products.jsonl"

# Current timestamp for filters
current_ts = int(time.time())

# ---------------------------
# Iterate through categories
# ---------------------------
for cat in category_tree:
    for subcat in cat.get("subcategories", []):
        # Check if sub-subcategories exist
        if subcat.get("sub_subcategories"):
            for sub_sub in subcat["sub_subcategories"]:
                # Determine end-level category ID
                if sub_sub.get("sub_subcategories"):
                    for end_sub in sub_sub["sub_subcategories"]:
                        end_category_id = end_sub.get("id")
                        end_category_name = end_sub.get("name")
                        print(f"Fetching products for end-level category: {end_category_id} | {end_category_name}")

                        # ---------------------------
                        # Build Algolia POST payload
                        # ---------------------------
                        payload = {
                            "query": "",
                            "clickAnalytics": True,
                            "analytics": True,
                            "hitsPerPage": 60,
                            "page": 0,
                            "removeWordsIfNoResults": "allOptional",
                            "optionalFilters": [f"STOCK.{end_category_id}:1"],
                            "attributesToRetrieve": [
                                "STATUS","BRAND","CIN","NAME","AVG_RATING","RATING_COUNT",
                                "ICONS","PRICES.EN","SALES_TYPE","MAX_QTY","STOCK.4565",
                                "IS_FROZEN","IS_BWS","PROMOS.EN","LABEL","LABEL_START_DATE",
                                "LABEL_END_DATE","IS_SPONSORED","PRODUCT_TYPE","CIN_ID",
                                "PRIMARY_TAXONOMY","IMAGE_ID","PACK_SIZE","PHARMACY_RESTRICTED",
                                "CS_YES","CS_TEXT","IS_FTO","PURCHASE_START_DATE_FTO",
                                "PURCHASE_END_DATE_FTO","DELIVERY_SLOT_START_DATE_FTO",
                                "END_DATE","START_DATE","SIZE_DESC","REWARDS","SHOW_PRICE_CS","ID"
                            ],
                            "facets":["NUTRITIONAL_INFO.*","BRAND"],
                            "filters": f"(STATUS:A OR STATUS:I) AND END_DATE>{current_ts}"
                        }

                        # ---------------------------
                        # FIRST REQUEST → get nbPages
                        # ---------------------------
                        response = requests.post(
                            'https://8i6wskccnv-dsn.algolia.net/1/indexes/ASDA_PRODUCTS/query?x-algolia-agent=Algolia%20for%20JavaScript%20(4.25.2)%3B%20Browser',
                            headers=headers,
                            data=json.dumps(payload),
                            impersonate="chrome131"
                        )

                        data = response.json()
                        nb_pages = data.get("nbPages", 0)
                        print(f"  Total pages: {nb_pages}")

                        # ---------------------------
                        # LOOP THROUGH PAGES
                        # ---------------------------
                        for page in range(nb_pages):
                            payload["page"] = page
                            resp = requests.post(
                                'https://8i6wskccnv-dsn.algolia.net/1/indexes/ASDA_PRODUCTS/query?x-algolia-agent=Algolia%20for%20JavaScript%20(4.25.2)%3B%20Browser',
                                headers=headers,
                                data=json.dumps(payload),
                                impersonate="chrome131"
                            )
                            page_data = resp.json()
                            products = page_data.get("hits", [])

                            for product in products:
                                product_data = {
                                    "product_id": product.get("ID"),
                                    "name": product.get("NAME"),
                                    "brand": product.get("BRAND"),
                                    "avg_rating": product.get("AVG_RATING"),
                                    "rating_count": product.get("RATING_COUNT"),
                                    "price": product.get("PRICES", {}).get("EN").get("PRICE"),
                                    "package_size":product.get("PACK_SIZE"),
                                    "shelf_name": product.get("PRIMARY_TAXONOMY", {}).get("SHELF_NAME"),
                                    "priceperuom":product.get("PRICES", {}).get("EN").get("PRICEPERUOM"),
                                    "currency":"GBP",
                                    "stock": product.get("STATUS"),
                                    "promos":product.get("POMOS")
                                }

#--------------------------------------parser-------------------------------------
from curl_cffi import requests
from parsel import Selector

url="https://www.asda.com/groceries/product/sausages/exceptional-by-asda-exceptional-6-lincolnshire-pork-sausages-400g/9111088"

response=requests.get(url,impersonate="chrome")
sel=Selector(response.text)
description=sel.xpath("//div[@data-testid='content']//text()").get()
image=sel.xpath("//script[@type='application/ld+json']//text()").get()#image containing script
print(description)


#---------------------------------extra api requests for breadcrumbs,upc etc------------------
from curl_cffi import requests

cookies = {
    '__cf_bm': '9ZZhVRToIYKVNG3lgG3mEkLwzEvGldcAgIEu5NwbAic-1765194552-1.0.1.1-ussUu.KMFu7cVYivO_bHkmaNaRRAigJ670_JTj6WEd2kJYZfcrGv.jRQlv_dVxE8Jji6OIdzl18K48xXHLuYZ6aEq6ZTNSe2j52DKy3QFn0',
    '_cfuvid': 'tz8cvUpNPZr2YQCqvOO7ZYdoToCRZ2_uflb6_LTYCo0-1765194552727-0.0.1.1-604800000',
    'SLAS.REFRESH_TOKEN': 'l6b6lvhgsxXuIxhwq99LK2d2h0S1SJT7GSnaEFIrJIw',
    'SLAS.ENC_USER_ID': 'adb831a7fdd83dd1e2a309ce7591dff8',
    'SLAS.USID': '91fd1c0b-9fdc-46b8-a6d0-6a50cb7dd783',
    'SLAS.CUSTOMER_ID': 'abmrdKxbdHkegRmuxIwWYYlKg2',
    'SLAS.AUTH_TOKEN': 'Bearer%20eyJ2ZXIiOiIxLjAiLCJqa3UiOiJzbGFzL3Byb2QvYmpnc19wcmQiLCJraWQiOiIxNmIwNWEwMS1iMGJlLTQ2ZWUtOTFmNS00ODQzMDkwZDAwOTAiLCJ0eXAiOiJqd3QiLCJjbHYiOiJKMi4zLjQiLCJhbGciOiJFUzI1NiJ9.eyJhdXQiOiJHVUlEIiwic2NwIjoic2ZjYy5zaG9wcGVyLW15YWNjb3VudC5iYXNrZXRzIHNmY2Muc2hvcHBlci1wcm9kdWN0cyBzZmNjLmludmVudG9yeS5hdmFpbGFiaWxpdHkucncgc2ZjYy5zaG9wcGVyLW15YWNjb3VudC5ydyBzZmNjLnNob3BwZXItY3VzdG9tZXJzLmxvZ2luIHNmY2Muc2hvcHBlci1jb250ZXh0LnJ3IHNmY2Muc2hvcHBlci1jdXN0b21lcnMucmVnaXN0ZXIgc2ZjYy5zaG9wcGVyLW15YWNjb3VudC5hZGRyZXNzZXMucncgc2ZjYy5zaG9wcGVyLW15YWNjb3VudC5wcm9kdWN0bGlzdHMucncgc2ZjYy5zaG9wcGVyLXByb21vdGlvbnMgc2ZjYy5zaG9wcGVyLWJhc2tldHMtb3JkZXJzLnJ3IHNmY2Muc2hvcHBlci1teWFjY291bnQucGF5bWVudGluc3RydW1lbnRzLnJ3IHNmY2Muc2hvcHBlci1jYXRlZ29yaWVzIGNfY3VzdG9tYXBpX3IiLCJzdWIiOiJjYy1zbGFzOjpiamdzX3ByZDo6c2NpZDplNjhjYTM2ZC02NTE2LTQ3MDQtYjcwNS0wNmI3NGY4NWVmMmU6OnVzaWQ6OTFmZDFjMGItOWZkYy00NmI4LWE2ZDAtNmE1MGNiN2RkNzgzIiwiY3R4Ijoic2xhcyIsImlzcyI6InNsYXMvcHJvZC9iamdzX3ByZCIsImlzdCI6MSwiZG50IjoiMCIsImF1ZCI6ImNvbW1lcmNlY2xvdWQvcHJvZC9iamdzX3ByZCIsIm5iZiI6MTc2NTE5NDcxNiwic3R5IjoiVXNlciIsImlzYiI6InVpZG86c2xhczo6dXBuOkd1ZXN0Ojp1aWRuOkd1ZXN0IFVzZXI6OmdjaWQ6YWJtcmRLeGJkSGtlZ1JtdXhJd1dZWWxLZzI6OmNoaWQ6QVNEQV9HUk9DRVJJRVMiLCJleHAiOjE3NjUxOTY1NDYsImlhdCI6MTc2NTE5NDc0NiwianRpIjoiQzJDLTEwMTYzMTg5MDE5MDg1MDUwMTg3NTA0MjAyMTA5NzMyMjg5In0.Kv_UiLnjebLF2cwbTM0SSb1Sahcf4FfNuXxpITCIoUkIwYZraqZCQ0e5K57KbvucRz9IUPpwXDsoQlcIQNXe4g',
    'cf_clearance': 'k12U.l0NspReRUBNX7HjDBlqPotRgtfE8ffwRCSCdUY-1765194750-1.2.1.1-xaufjQz6o_xzRQZ5KUHHItqeP.6OOBfce1Jcogvh_CPKXbxFiwRYwA9l0yGtILZmQSE7iM4.LLjDC0DKgvVAuzqQfN6dADlMx2gC_SxptO4F4TJiTa1X.trnq9hemxgXMGnVvGAbqDJd5NCOoZQOsgpp58YbExjbB4muYlaMXG5RfZywb9GTJ2qeFX5kXoQGhMEtMmrFbrVaI6p512q7XC4CaXJAiY3mKYdf439JJJ8',
    '_mibhv': 'anon-1765194750438-9242323532_8338',
    'BVImplmain_site': '11603',
    'kndctr_B9CB1CFE53309CAD0A490D45_AdobeOrg_consent': 'general=out',
    'kndctr_B9CB1CFE53309CAD0A490D45_AdobeOrg_identity': 'CiY2OTg0OTc4ODE1MzMwMjM2NTk1MjU2OTIwMzQwMzIxMjk2ODI2MlIRCIOwue6vMxgBKgRJTkQxMAHwAYOwue6vMw==',
    'kndctr_B9CB1CFE53309CAD0A490D45_AdobeOrg_cluster': 'ind1',
    'OptanonAlertBoxClosed': '2025-12-08T11:52:37.143Z',
    'eupubconsent-v2': 'CQcI1f9QcI1f9AcABBENDgCgAAAAAAAAAChQAAAAAAAA.YAAAAAAAAAAA',
    'previousPageName': 'pdp-page',
    'visitorId': 'ea562eb0-ebfa-41ce-9967-cf6b9290b98f',
    'OptanonConsent': 'isIABGlobal=false&datestamp=Mon+Dec+08+2025+17%3A29%3A41+GMT%2B0530+(India+Standard+Time)&version=6.29.0&hosts=&landingPath=NotLandingPage&groups=1%3A1%2C2%3A0%2C4%3A0%2C5%3A0%2CSTACK42%3A0&geolocation=IN%3BKL&AwaitingReconsent=false',
    'da_sid': 'C315BA7B8EADAE10721AAA13AEABB6744D.0|4|0|3',
    'da_lid': 'F02689489AEDEA8BE74BBB99ECA9FC7FFE|0|0|0',
    'da_intState': '',
}

headers = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'authorization': 'Bearer eyJ2ZXIiOiIxLjAiLCJqa3UiOiJzbGFzL3Byb2QvYmpnc19wcmQiLCJraWQiOiIxNmIwNWEwMS1iMGJlLTQ2ZWUtOTFmNS00ODQzMDkwZDAwOTAiLCJ0eXAiOiJqd3QiLCJjbHYiOiJKMi4zLjQiLCJhbGciOiJFUzI1NiJ9.eyJhdXQiOiJHVUlEIiwic2NwIjoic2ZjYy5zaG9wcGVyLW15YWNjb3VudC5iYXNrZXRzIHNmY2Muc2hvcHBlci1wcm9kdWN0cyBzZmNjLmludmVudG9yeS5hdmFpbGFiaWxpdHkucncgc2ZjYy5zaG9wcGVyLW15YWNjb3VudC5ydyBzZmNjLnNob3BwZXItY3VzdG9tZXJzLmxvZ2luIHNmY2Muc2hvcHBlci1jb250ZXh0LnJ3IHNmY2Muc2hvcHBlci1jdXN0b21lcnMucmVnaXN0ZXIgc2ZjYy5zaG9wcGVyLW15YWNjb3VudC5hZGRyZXNzZXMucncgc2ZjYy5zaG9wcGVyLW15YWNjb3VudC5wcm9kdWN0bGlzdHMucncgc2ZjYy5zaG9wcGVyLXByb21vdGlvbnMgc2ZjYy5zaG9wcGVyLWJhc2tldHMtb3JkZXJzLnJ3IHNmY2Muc2hvcHBlci1teWFjY291bnQucGF5bWVudGluc3RydW1lbnRzLnJ3IHNmY2Muc2hvcHBlci1jYXRlZ29yaWVzIGNfY3VzdG9tYXBpX3IiLCJzdWIiOiJjYy1zbGFzOjpiamdzX3ByZDo6c2NpZDplNjhjYTM2ZC02NTE2LTQ3MDQtYjcwNS0wNmI3NGY4NWVmMmU6OnVzaWQ6OTFmZDFjMGItOWZkYy00NmI4LWE2ZDAtNmE1MGNiN2RkNzgzIiwiY3R4Ijoic2xhcyIsImlzcyI6InNsYXMvcHJvZC9iamdzX3ByZCIsImlzdCI6MSwiZG50IjoiMCIsImF1ZCI6ImNvbW1lcmNlY2xvdWQvcHJvZC9iamdzX3ByZCIsIm5iZiI6MTc2NTE5NDcxNiwic3R5IjoiVXNlciIsImlzYiI6InVpZG86c2xhczo6dXBuOkd1ZXN0Ojp1aWRuOkd1ZXN0IFVzZXI6OmdjaWQ6YWJtcmRLeGJkSGtlZ1JtdXhJd1dZWWxLZzI6OmNoaWQ6QVNEQV9HUk9DRVJJRVMiLCJleHAiOjE3NjUxOTY1NDYsImlhdCI6MTc2NTE5NDc0NiwianRpIjoiQzJDLTEwMTYzMTg5MDE5MDg1MDUwMTg3NTA0MjAyMTA5NzMyMjg5In0.Kv_UiLnjebLF2cwbTM0SSb1Sahcf4FfNuXxpITCIoUkIwYZraqZCQ0e5K57KbvucRz9IUPpwXDsoQlcIQNXe4g',
    'cache-control': 'no-store',
    'content-type': 'application/json',
    'correlation-id': '60f3d977-af5a-4a88-b2bb-19a3e1d3f075',
    'newrelic': 'eyJ2IjpbMCwxXSwiZCI6eyJ0eSI6IkJyb3dzZXIiLCJhYyI6IjM4NjYwNzciLCJhcCI6IjExMjAyNDk5MjUiLCJpZCI6IjQwMTMwMDg3ZjAxM2IyZjEiLCJ0ciI6ImY2Y2RjMzNlZmU4MDg5YmE3NWRmYmM5ZDNiOTg3ODFjIiwidGkiOjE3NjUxOTUyMDE2ODIsInRrIjoiMzgzNTIyNSJ9fQ==',
    'pragma': 'no-store',
    'priority': 'u=1, i',
    'referer': 'https://www.asda.com/groceries/product/baby-new-potatoes/exceptional-by-asda-british-baby-potatoes-1kg/9247574',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'traceparent': '00-f6cdc33efe8089ba75dfbc9d3b98781c-40130087f013b2f1-01',
    'tracestate': '3835225@nr=0-1-3866077-1120249925-40130087f013b2f1----1765195201682',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'x-apisession-id': '0db7e7e2-00ff-4240-9b11-9939cfc07fec',
    # 'cookie': '__cf_bm=9ZZhVRToIYKVNG3lgG3mEkLwzEvGldcAgIEu5NwbAic-1765194552-1.0.1.1-ussUu.KMFu7cVYivO_bHkmaNaRRAigJ670_JTj6WEd2kJYZfcrGv.jRQlv_dVxE8Jji6OIdzl18K48xXHLuYZ6aEq6ZTNSe2j52DKy3QFn0; _cfuvid=tz8cvUpNPZr2YQCqvOO7ZYdoToCRZ2_uflb6_LTYCo0-1765194552727-0.0.1.1-604800000; SLAS.REFRESH_TOKEN=l6b6lvhgsxXuIxhwq99LK2d2h0S1SJT7GSnaEFIrJIw; SLAS.ENC_USER_ID=adb831a7fdd83dd1e2a309ce7591dff8; SLAS.USID=91fd1c0b-9fdc-46b8-a6d0-6a50cb7dd783; SLAS.CUSTOMER_ID=abmrdKxbdHkegRmuxIwWYYlKg2; SLAS.AUTH_TOKEN=Bearer%20eyJ2ZXIiOiIxLjAiLCJqa3UiOiJzbGFzL3Byb2QvYmpnc19wcmQiLCJraWQiOiIxNmIwNWEwMS1iMGJlLTQ2ZWUtOTFmNS00ODQzMDkwZDAwOTAiLCJ0eXAiOiJqd3QiLCJjbHYiOiJKMi4zLjQiLCJhbGciOiJFUzI1NiJ9.eyJhdXQiOiJHVUlEIiwic2NwIjoic2ZjYy5zaG9wcGVyLW15YWNjb3VudC5iYXNrZXRzIHNmY2Muc2hvcHBlci1wcm9kdWN0cyBzZmNjLmludmVudG9yeS5hdmFpbGFiaWxpdHkucncgc2ZjYy5zaG9wcGVyLW15YWNjb3VudC5ydyBzZmNjLnNob3BwZXItY3VzdG9tZXJzLmxvZ2luIHNmY2Muc2hvcHBlci1jb250ZXh0LnJ3IHNmY2Muc2hvcHBlci1jdXN0b21lcnMucmVnaXN0ZXIgc2ZjYy5zaG9wcGVyLW15YWNjb3VudC5hZGRyZXNzZXMucncgc2ZjYy5zaG9wcGVyLW15YWNjb3VudC5wcm9kdWN0bGlzdHMucncgc2ZjYy5zaG9wcGVyLXByb21vdGlvbnMgc2ZjYy5zaG9wcGVyLWJhc2tldHMtb3JkZXJzLnJ3IHNmY2Muc2hvcHBlci1teWFjY291bnQucGF5bWVudGluc3RydW1lbnRzLnJ3IHNmY2Muc2hvcHBlci1jYXRlZ29yaWVzIGNfY3VzdG9tYXBpX3IiLCJzdWIiOiJjYy1zbGFzOjpiamdzX3ByZDo6c2NpZDplNjhjYTM2ZC02NTE2LTQ3MDQtYjcwNS0wNmI3NGY4NWVmMmU6OnVzaWQ6OTFmZDFjMGItOWZkYy00NmI4LWE2ZDAtNmE1MGNiN2RkNzgzIiwiY3R4Ijoic2xhcyIsImlzcyI6InNsYXMvcHJvZC9iamdzX3ByZCIsImlzdCI6MSwiZG50IjoiMCIsImF1ZCI6ImNvbW1lcmNlY2xvdWQvcHJvZC9iamdzX3ByZCIsIm5iZiI6MTc2NTE5NDcxNiwic3R5IjoiVXNlciIsImlzYiI6InVpZG86c2xhczo6dXBuOkd1ZXN0Ojp1aWRuOkd1ZXN0IFVzZXI6OmdjaWQ6YWJtcmRLeGJkSGtlZ1JtdXhJd1dZWWxLZzI6OmNoaWQ6QVNEQV9HUk9DRVJJRVMiLCJleHAiOjE3NjUxOTY1NDYsImlhdCI6MTc2NTE5NDc0NiwianRpIjoiQzJDLTEwMTYzMTg5MDE5MDg1MDUwMTg3NTA0MjAyMTA5NzMyMjg5In0.Kv_UiLnjebLF2cwbTM0SSb1Sahcf4FfNuXxpITCIoUkIwYZraqZCQ0e5K57KbvucRz9IUPpwXDsoQlcIQNXe4g; cf_clearance=k12U.l0NspReRUBNX7HjDBlqPotRgtfE8ffwRCSCdUY-1765194750-1.2.1.1-xaufjQz6o_xzRQZ5KUHHItqeP.6OOBfce1Jcogvh_CPKXbxFiwRYwA9l0yGtILZmQSE7iM4.LLjDC0DKgvVAuzqQfN6dADlMx2gC_SxptO4F4TJiTa1X.trnq9hemxgXMGnVvGAbqDJd5NCOoZQOsgpp58YbExjbB4muYlaMXG5RfZywb9GTJ2qeFX5kXoQGhMEtMmrFbrVaI6p512q7XC4CaXJAiY3mKYdf439JJJ8; _mibhv=anon-1765194750438-9242323532_8338; BVImplmain_site=11603; kndctr_B9CB1CFE53309CAD0A490D45_AdobeOrg_consent=general=out; kndctr_B9CB1CFE53309CAD0A490D45_AdobeOrg_identity=CiY2OTg0OTc4ODE1MzMwMjM2NTk1MjU2OTIwMzQwMzIxMjk2ODI2MlIRCIOwue6vMxgBKgRJTkQxMAHwAYOwue6vMw==; kndctr_B9CB1CFE53309CAD0A490D45_AdobeOrg_cluster=ind1; OptanonAlertBoxClosed=2025-12-08T11:52:37.143Z; eupubconsent-v2=CQcI1f9QcI1f9AcABBENDgCgAAAAAAAAAChQAAAAAAAA.YAAAAAAAAAAA; previousPageName=pdp-page; visitorId=ea562eb0-ebfa-41ce-9967-cf6b9290b98f; OptanonConsent=isIABGlobal=false&datestamp=Mon+Dec+08+2025+17%3A29%3A41+GMT%2B0530+(India+Standard+Time)&version=6.29.0&hosts=&landingPath=NotLandingPage&groups=1%3A1%2C2%3A0%2C4%3A0%2C5%3A0%2CSTACK42%3A0&geolocation=IN%3BKL&AwaitingReconsent=false; da_sid=C315BA7B8EADAE10721AAA13AEABB6744D.0|4|0|3; da_lid=F02689489AEDEA8BE74BBB99ECA9FC7FFE|0|0|0; da_intState=',
}

params = {
    'siteId': 'ASDA_GROCERIES',
    'allImages': 'true',
    'c_isPDP': 'true',
}

response = requests.get(
    'https://www.asda.com/mobify/proxy/ghs-api/product/shopper-products/v1/organizations/f_ecom_bjgs_prd/products/4778498',
    
    params=params,
    #cookies=cookies,
    headers=headers,
    impersonate='chrome110',
)

print("Status Code:", response.status_code)
print(response.json())


#-------------------findings-------------------------------------------------------------
# 1.403 errors occurred using simple requests due to Cloudflare protection; resolved using curl_cffi.

# 2.Category data extraction is complex, requiring extra API requests for each subcategory.

# 3.PDP URLs need to be generated using name, ID, and category.(sometimes may fail)
