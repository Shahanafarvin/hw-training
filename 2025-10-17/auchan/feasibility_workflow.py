import requests
import unicodedata
import re
################################category api urls to crawl products################################
headers = {
    "accept": "application/json",
    "accept-language": "hu",
    "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI4cG1XclQzWmxWMUFJbXdiMUhWYWE5T1BWSzkzcjhIcyIsImp0aSI6IjgwOTk3M2ZlNzAyNzYzMGE1ZTZkZjQ5MjQ5MmRhNmE0MjhhYzNhNTk1ZmViNTRhYzI2NDI2Y2MxZDdkNzdjNzgzMjc5ZjMxYmJkMWQ2NjFmIiwiaWF0IjoxNzYxMDIzMDY1LjMzOTkzMywibmJmIjoxNzYxMDIzMDY1LjMzOTkzNiwiZXhwIjoxNzYxMTA5NDY1LjMxNTQxLCJzdWIiOiJhbm9uXzNjNTkxZjM4LTMyNDItNDJjOS04ZTNmLTZmNjgwYTJkOTEzOSIsInNjb3BlcyI6W119.k1quA-b6_p1rNqYs7Y4hhRRPqz2rICfjSAb8dEJZoOp46njyn0gpjPyIq_533jTmDjyxMWrzkGxyxjd1E0xKUPGDu461_DRdzQ97SnEEISuaRGXrztymIjN43OZ4K2VLO1sx3rH3T50sB9_Y5kUSYJPgvxLHikzCzWMe9fAKrzX65xmA4JbPiXhKxo58SF-izGgCHHekNyCu2pDXf9Qqa4g_Npc2CzEGcr24RyPY6zwGDA-0G_jTeKO9WfjuZcrXH5ZAtQjbUp0tJ6pUXiS9-07rJvcCS5eEPjoX2uz0enQJk9hKp4gquDaA88GzCBYSzqBAS81jyaLZmI_okdymzQ",
    "cache-control": "no-cache",
    "referer": "https://auchan.hu/",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
}
rurl = "https://auchan.hu/api/v2/cache/tree/0?depth=1&cacheSegmentationCode=&hl=hu"

response = requests.get(url, headers=HEADERS, timeout=15)
response.raise_for_status()

data = response.json()
for cat in data.get("children", []):
    if cat.get("boutique", True) is False:
        cat_id = cat.get("id")
        cat_name = cat.get("name")
        child_count = cat.get("childCount", 0)

        # Recursively get subcategories
        subcategories = fetch_subcategories(cat_id) if child_count != 0 else []  # function recursuively fetches subcategories

        
##############################CRAWLER##############################
urls = [
    "https://auchan.hu/api/v2/cache/products?categoryId=15398&page=1&itemsPerPage=12&filters%5B%5D=available&filterValues%5B%5D=1&cacheSegmentationCode=&hl=hu",
    "https://auchan.hu/api/v2/cache/products?categoryId=15401&page=1&itemsPerPage=12&filters%5B%5D=available&filterValues%5B%5D=1&cacheSegmentationCode=&hl=hu"
] #sample category api urls

headers = {
    "accept": "application/json",
    "accept-language": "hu",
    "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI4cG1XclQzWmxWMUFJbXdiMUhWYWE5T1BWSzkzcjhIcyIsImp0aSI6IjM3MTRkMzhlNTliMzJlMmIzMzNiMDhhYjk2M2U2Y2QwZTM3YTQwOWI5NDM3YmNhZDZjNjRlMDdmNmFiMTUwMGFmM2E0NTUxOGMxMjJjMWIyIiwiaWF0IjoxNzYxMjE5NzA3Ljc5ODU0NiwibmJmIjoxNzYxMjE5NzA3Ljc5ODU0OCwiZXhwIjoxNzYxMzA2MTA3Ljc3NjIxMywic3ViIjoiYW5vbl82YWI0MGM3Zi1hZjNjLTRkMWItOWQwNy0wYzk1MDU0N2Q1ZjkiLCJzY29wZXMiOltdfQ.Rx9npOZNknzGPUqrVx7IJ2Q3hIoXKJttBWMAmjfjNbv799JWHEzFtWauJrfyEV027jkballQjGcf2xqDOi1YlvisFu1pD0kA7wzWJU0AfV3_GnlhHwBwpeKWqt_tYZtylIYo28i9A7_mbgNfxWQp5KCu5LV7Smem7SAyDWlVto7aqUtouAGHvb0PI9_2fE4YYq8h1COTzUcPjNosS1lfqShyuyL-DUUfme7oziPcmUftdFsgFZ0ir7dTwI279ZPW1XJpExJKsezydfOEQQpC2ilrGxUcfFjCjjyBSBwGtDq0Gxw8GwiW7hCiSd7VSeAwEs2bG_TR-7MzzKw9vWLAaA",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
}

all_products = []

for url in urls:
    response = requests.get(url,headers=headers)
    print("Status Code:", response.status_code)
    data = response.json()

    for item in data.get("results", []):
        name=item.get("selectedVariant",{}).get("name")
        sku=item.get("selectedVariant",{}).get("sku")
        # Normalize accents (e.g., á → a)
        slug = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
        # Lowercase and replace spaces/special chars
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', slug.strip().lower())
        all_products.append({
            "brand": item.get("brandName"),
            "breadcrumbs":" > ".join([cat.get("name", "") for cat in item.get("categories",[]) if "name" in cat]),
            "images": item.get("selectedVariant",{}).get("media",{}).get("images"),
            "title":name,
            "grammage_quantity": item.get("selectedVariant",{}).get("packageInfo",{}).get("packageSize"),
            "grammage_unit":item.get("selectedVariant",{}).get("packageInfo",{}).get("packageUnit"),
            "unit_price":item.get("selectedVariant",{}).get("packageInfo",{}).get("unitPrice",{}).get("net"),
            "regular_price":item.get("selectedVariant",{}).get("price",{}).get("net"),
            "currency":item.get("selectedVariant",{}).get("price",{}).get("currency"),
            "sku":sku,
            "product_id":item.get("selectedVariant",{}).get("productId"),
            "selectvalue":item.get("selectedVariant",{}).get("selectValue"),
            "details":item.get("selectedVariant",{}).get("details"),
            "product_url":f"https://auchan.hu/shop/{slug}.p-{sku}",
        
        })
    page_count = data.get("pageCount", 1)#paginate using this total page count

##############################additional requests for each product##############################
headers = {
    "accept": "application/json",
    "accept-language": "hu",
    "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI4cG1XclQzWmxWMUFJbXdiMUhWYWE5T1BWSzkzcjhIcyIsImp0aSI6IjgwOTk3M2ZlNzAyNzYzMGE1ZTZkZjQ5MjQ5MmRhNmE0MjhhYzNhNTk1ZmViNTRhYzI2NDI2Y2MxZDdkNzdjNzgzMjc5ZjMxYmJkMWQ2NjFmIiwiaWF0IjoxNzYxMDIzMDY1LjMzOTkzMywibmJmIjoxNzYxMDIzMDY1LjMzOTkzNiwiZXhwIjoxNzYxMTA5NDY1LjMxNTQxLCJzdWIiOiJhbm9uXzNjNTkxZjM4LTMyNDItNDJjOS04ZTNmLTZmNjgwYTJkOTEzOSIsInNjb3BlcyI6W119.k1quA-b6_p1rNqYs7Y4hhRRPqz2rICfjSAb8dEJZoOp46njyn0gpjPyIq_533jTmDjyxMWrzkGxyxjd1E0xKUPGDu461_DRdzQ97SnEEISuaRGXrztymIjN43OZ4K2VLO1sx3rH3T50sB9_Y5kUSYJPgvxLHikzCzWMe9fAKrzX65xmA4JbPiXhKxo58SF-izGgCHHekNyCu2pDXf9Qqa4g_Npc2CzEGcr24RyPY6zwGDA-0G_jTeKO9WfjuZcrXH5ZAtQjbUp0tJ6pUXiS9-07rJvcCS5eEPjoX2uz0enQJk9hKp4gquDaA88GzCBYSzqBAS81jyaLZmI_okdymzQ",
    "cache-control": "no-cache",
    "referer": "https://auchan.hu/shop/alpro-bananos-szojaital-250-ml.p-380610",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
}

cookies = {
    "isWebpFormatSupportedAlgo0": "true",
    "login_type": "anon",
    "token_type": "Bearer",
   
}
products = [
    {
    "brand": "La fiesta",
    "breadcrumbs": "Italok > Bor > Hazai borok > Fehér",
    "images": [
      "https://ahuazurewebblob0-d2geauehc9ekc7ey.z01.azurefd.net/auchan/cache/product_medium/product/33918885/01_309388_front_1551018512.png"
    ],
    "title": "La Fiesta rajnai rizling száraz fehér tájbor, 0,75 l (425024)",
    "grammage_quantity": 0.75,
    "grammage_unit": "LITER",
    "unit_price": 1039,
    "regular_price": 779,
    "currency": "HUF",
    "sku": "425024",
    "product_id": 10762,
    "selectvalue": 10765,
    "details": [
      "description",
      "ingredients",
      "parameterList",
      "allergens"
    ],
    "product_url": "https://auchan.hu/shop/la-fiesta-rajnai-rizling-szaraz-feher-tajbor-0-75-l-425024-.p-425024"
  }
]


all_details = []
for p in products:
    for detail in p.get("details", []):
        if detail == "description":
            url = f"https://auchan.hu/api/v2/cache/products/{p['product_id']}/variants/{p['selectvalue']}/details/description?hl=hu"
        elif detail == "parameterList":
            url = f"https://auchan.hu/api/v2/cache/products/{p['product_id']}/variants/{p['selectvalue']}/details/parameterList?hl=hu"
        elif detail == "ingredients":
            url = f"https://auchan.hu/api/v2/cache/products/{p['product_id']}/variants/{p['selectvalue']}/details/ingredients?hl=hu"
        elif detail == "nutrition":
            url = f"https://auchan.hu/api/v2/cache/products/{p['product_id']}/variants/{p['selectvalue']}/details/nutrition?hl=hu"
        elif detail == "allergens":
            url = f"https://auchan.hu/api/v2/cache/products/{p['product_id']}/variants/{p['selectvalue']}/details/allergensDetailed?hl=hu"
        else:
            continue  # additional detail types can be handled here
        response = requests.get(url,headers=headers, cookies=cookies)
        print("Requesting:", url, "→", response.status_code)

        if response.status_code == 200:
            desc_data = response.json()
            #print("Detail data:", desc_data)
            if detail == "description":
                p["description"] = desc_data.get("description", "")
            if detail == "parameterList": 
                p["parameters"] = desc_data.get("parameters", [])
            if detail == "ingredients":
                p["ingredients"] = desc_data.get("description", "")
            if detail == "nutrition":
                p["nutrition"] = desc_data.get("nutritions", {}).get("data", [])
            if detail == "allergens":
                p["allergens"] = ",".join([allergen.get("name", "") for allergen in desc_data.get("allergensDetailed",[]) if "name" in allergen])
            all_details.append(p)



##############################FINDINGS##############################
# No product URLs found in the PLP page HTML; content is dynamically loaded through API calls. 
# need to handle deep recursive API calls to fetch all nested subcategories
# Each product extracted from the PLP page requires an additional average of 3 API requests to retrieve details such as description, features, ingredients etc
# Category API URLs need to be generated, as they are available across different API requests.
# product URLs need to be generated, as they are not provided explicitly or via slugs