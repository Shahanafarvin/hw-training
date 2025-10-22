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
root_url = "https://auchan.hu/api/v2/cache/tree/0?depth=1&cacheSegmentationCode=&hl=hu"
response = requests.get(root_url, headers=headers)
print("Requesting root categories:", response.status_code)

if response.status_code == 200:
    data = response.json()
    categories = data.get("children", [])
    for cat in categories:
        cat_id = cat.get("id")
        cat_name = cat.get("name")
        product_count = cat.get("productCount", 0)
        category_api = f"https://auchan.hu/api/v2/cache/tree/{cat_id}?depth=1&cacheSegmentationCode=&hl=hu"
        category_products_api = f"https://auchan.hu/api/v2/cache/products?categoryId={cat_id}&page=1&itemsPerPage=12&filters[]=available&filterValues[]=1&cacheSegmentationCode=&hl=hu"

        sub_resp = requests.get(category_api, headers=headers)
        subcategories_list = []

        if sub_resp.status_code == 200:
            sub_data = sub_resp.json()
            sub_children = sub_data.get("children", [])
            for sub in sub_children:
                sub_id = sub.get("id")
                sub_name = sub.get("name")
                sub_count = sub.get("productCount", 0)
                sub_api_url = f"https://auchan.hu/api/v2/cache/products?categoryId={sub_id}&page=1&itemsPerPage=12&filters[]=available&filterValues[]=1&cacheSegmentationCode=&hl=hu"

                subcategories_list.append({
                    "sub_id": sub_id,
                    "sub_name": sub_name,
                    "sub_product_count": sub_count,
                    "subcategory_api": sub_api_url
                })
##############################CRAWLER##############################
urls = [
    "https://auchan.hu/api/v2/cache/products?categoryId=15398&page=1&itemsPerPage=12&filters%5B%5D=available&filterValues%5B%5D=1&cacheSegmentationCode=&hl=hu",
    "https://auchan.hu/api/v2/cache/products?categoryId=15401&page=1&itemsPerPage=12&filters%5B%5D=available&filterValues%5B%5D=1&cacheSegmentationCode=&hl=hu"
] #sample category api urls

headers = {
    "accept": "application/json",
    "accept-language": "hu",
    "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI4cG1XclQzWmxWMUFJbXdiMUhWYWE5T1BWSzkzcjhIcyIsImp0aSI6IjgwOTk3M2ZlNzAyNzYzMGE1ZTZkZjQ5MjQ5MmRhNmE0MjhhYzNhNTk1ZmViNTRhYzI2NDI2Y2MxZDdkNzdjNzgzMjc5ZjMxYmJkMWQ2NjFmIiwiaWF0IjoxNzYxMDIzMDY1LjMzOTkzMywibmJmIjoxNzYxMDIzMDY1LjMzOTkzNiwiZXhwIjoxNzYxMTA5NDY1LjMxNTQxLCJzdWIiOiJhbm9uXzNjNTkxZjM4LTMyNDItNDJjOS04ZTNmLTZmNjgwYTJkOTEzOSIsInNjb3BlcyI6W119.k1quA-b6_p1rNqYs7Y4hhRRPqz2rICfjSAb8dEJZoOp46njyn0gpjPyIq_533jTmDjyxMWrzkGxyxjd1E0xKUPGDu461_DRdzQ97SnEEISuaRGXrztymIjN43OZ4K2VLO1sx3rH3T50sB9_Y5kUSYJPgvxLHikzCzWMe9fAKrzX65xmA4JbPiXhKxo58SF-izGgCHHekNyCu2pDXf9Qqa4g_Npc2CzEGcr24RyPY6zwGDA-0G_jTeKO9WfjuZcrXH5ZAtQjbUp0tJ6pUXiS9-07rJvcCS5eEPjoX2uz0enQJk9hKp4gquDaA88GzCBYSzqBAS81jyaLZmI_okdymzQ",
    "referer": "https://auchan.hu/shop/italok.c-14740",
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
# Each product extracted from the PLP page requires an additional average of 3 API requests to retrieve details such as description, features, ingredients etc
# No product URLs found in the PLP page HTML; content is dynamically loaded through API calls. 
# Category API URLs need to be generated, as they are available across different API requests.
# product URLs need to be generated, as they are not provided explicitly or via slugs