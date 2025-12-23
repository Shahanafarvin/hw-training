import requests
import math
import json
import time
import random


#----------------------------------crawler---------------------------------------------------------------#
headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://www.3m.com/3M/en_US/p/',
    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'snaps-override_7': 'snapsPageUniqueName=CORP_SNAPS_GPH_US',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'x-dtpc': '3$67527056_22h21vRKFUCAHWATRUKRKVPJKUWRBPGEDQDTFC-0e0',
}


BASE_URL = "https://www.3m.com/snaps2/api/pcp-show-next/https/www.3m.com/3M/en_US/p/"
PAGE_SIZE = 51
MAX_RETRIES = 3

start = 0

# ---- First request (discover total) ----
params = {
    "size": PAGE_SIZE,
    "start": start,
}

response = requests.get(BASE_URL, params=params, headers=headers)
response.raise_for_status()

data = response.json()

total_products = data.get("total")

total_pages = math.ceil(total_products / PAGE_SIZE)


items = data.get("items", [])

# ---- Pagination ----
for page in range(1, total_pages):
    start = page * PAGE_SIZE

    params = {
        "size": PAGE_SIZE,
        "start": start,
    }

    retries = 0
    while retries < MAX_RETRIES:
        delay = random.uniform(2, 4)
        time.sleep(delay)

        response = requests.get(BASE_URL, params=params, headers=headers)

        # ---- Stop conditions ----
        if response.status_code == 404:
            print(f"End of products at start={start}")
            page = total_pages
            break

        if response.status_code in (429, 503):
            retries += 1
            print(
                f"Server busy ({response.status_code}) at start={start}, "
                f"retry {retries}/{MAX_RETRIES}"
            )
            time.sleep(5 * retries)
            continue

        response.raise_for_status()
        break
    else:
        print(f"Skipping start={start} after {MAX_RETRIES} retries")
        continue

    data = response.json()
    items = data.get("items", [])
    final_products = []
    for item in items:
        final_products.append({
            "name": item.get("name"),
            "productNumber": item.get("productNumber"),
            "stockNumber": item.get("stockNumber"),
            "upc": item.get("upc"),
            "url": item.get("url"),
        })



#----------------------------------------------parser-------------------------------------------------------

from curl_cffi import requests
from parsel import Selector 


url="https://www.3m.com/3M/en_US/p/d/v000194562/" 
response = requests.get(url,impersonate="chrome") 
print(response.status_code) 

sel=Selector(response.text) 

breadcrumbs=" > ".join(sel.xpath("//ol[@class='MMM--breadcrumbs-list']/li//text()").getall()) 
print("Breadcrumbs:",breadcrumbs)

highlights=",".join(sel.xpath("//li[@class='sps2-pdp_details--highlights_item mds-font_paragraph']//text()").getall())
print(highlights)


des=",".join(sel.xpath("//div[@class='sps2-pdp_details--white_container']//text()").getall())
print(des)

suggested_appp=",".join(sel.xpath("//div[@class='sps2-pdp_details--section']//text()").getall())
print(suggested_appp)

script_tag=sel.xpath("//script/text()").getall()
for script in script_tag:
    if script.startswith("window.__INITIAL_DATA ="):
        json_data = script.replace("window.__INITIAL_DATA = ", "").strip().rstrip(";")
        data = json.loads(json_data)
        print(data.get("classificationAttributes"))

images=",".join(sel.xpath("//div[@class='sps2-pdp_outerGallery--container']//img/@src").getall())
print(images)  #all images are not extracted,some  are missing or js rendered



#------------------------------------findings---------------------------------------------------#
#1. Breadcrumbs,highlights,description,suggested application,classification attributes are extracted successfully.
#2. Some images are missing because they are js rendered.
#3. 1.Pagination rate limiting was encountered around the 196th page, with only 9,996 products extracted, 
# and it is unclear whether this is the final page or not.

#4.The PLP page uses a Show More pattern, so the API approach was selected.

#5.Specifications, resources, and rating details are JavaScript-rendered.