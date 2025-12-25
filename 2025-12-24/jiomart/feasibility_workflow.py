import requests
import time
import ast
import json
import time
import requests
from parsel import Selector

#------------------------------------------------------crawler--------------------------------------------------------------------------
cookies = {
    'AKA_A2': 'A',
    'nms_mgo_city': 'Mumbai',
    'nms_mgo_state_code': 'MH',
    'WZRK_G': '0c50d4f36c2346edaa505fb45de11fc1',
    '_fbp': 'fb.1.1766557996359.244939257',
    '_gcl_au': '1.1.1269692634.1766557997',
    '_ga': 'GA1.1.921928667.1766557997',
    'nms_mgo_pincode': '400054',
    'RT': '"z=1&dm=www.jiomart.com&si=28169922-12e9-42de-b3c4-81979c1a2143&ss=mjjn0lxt&sl=4&tt=64y&obo=2&rl=1"',
    '__tr_luptv': '1766558409819',
    'WZRK_S_88R-W4Z-495Z': '%7B%22p%22%3A5%2C%22s%22%3A1766557995%2C%22t%22%3A1766559050%7D',
    '_ga_XHR9Q2M3VV': 'GS2.1.s1766557997$o1$g1$t1766559095$j9$l0$h276523973',
}

headers = {
    'accept': '*/*',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'content-type': 'application/json',
    'origin': 'https://www.jiomart.com',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://www.jiomart.com/c/groceries/biscuits-drinks-packaged-foods/tea-coffee/29009',
    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
}

json_data = {
    'pageSize': 50,
    'facetSpecs': [
        {
            'facetKey': {
                'key': 'brands',
            },
            'limit': 500,
            'excludedFilterKeys': [
                'brands',
            ],
        },
        {
            'facetKey': {
                'key': 'categories',
            },
            'limit': 500,
            'excludedFilterKeys': [
                'categories',
            ],
        },
        {
            'facetKey': {
                'key': 'attributes.category_level_4',
            },
            'limit': 500,
            'excludedFilterKeys': [
                'attributes.category_level_4',
            ],
        },
        {
            'facetKey': {
                'key': 'attributes.category_level_1',
            },
            'excludedFilterKeys': [
                'attributes.category_level_4',
            ],
        },
        {
            'facetKey': {
                'key': 'attributes.avg_selling_price',
                'return_min_max': True,
                'intervals': [
                    {
                        'minimum': 0.1,
                        'maximum': 100000000,
                    },
                ],
            },
        },
        {
            'facetKey': {
                'key': 'attributes.avg_discount_pct',
                'return_min_max': True,
                'intervals': [
                    {
                        'minimum': 0,
                        'maximum': 99,
                    },
                ],
            },
        },
    ],
    'variantRollupKeys': [
        'variantId',
    ],
    'branch': 'projects/sr-project-jiomart-jfront-prod/locations/global/catalogs/default_catalog/branches/0',
    'pageCategories': [
        '29009',
    ],
    'userInfo': {
        'userId': None,
    },
    'pageToken': '4EGZ2IWZ3QTNmRDZtYGZxgTL3IjNy0CMwADMtYTNyUDN1kjNkoxA9Gb_cChBK77gCjADSADMxMgC',
    'orderBy': 'attributes.popularity desc',
    'filter': 'attributes.status:ANY("active") AND attributes.category_ids:ANY("29009") AND (attributes.available_regions:ANY("TXCF", "PANINDIAGROCERIES")) AND (attributes.inv_stores_1p:ANY("ALL", "T7GZ") OR attributes.inv_stores_3p:ANY("ALL", "groceries_zone_non-essential_services", "general_zone", "groceries_zone_essential_services"))',
    'visitorId': 'anonymous-16b88074-4641-4f8e-b5f9-c4e9141e3536',
}

all_products = []
page = 1

while True:
    response = requests.post('https://www.jiomart.com/trex/search', cookies=cookies, headers=headers, json=json_data)

    if response.status_code != 200:
        print("Request failed:", response.status_code)
        break

    data = response.json()

    # ---- Extract products ----
    products = data.get("results", [])
    if not products:
        print("No products found, stopping pagination.")
        break
    for product in products:
        variants = product.get("product", {}).get("variants", [])

        product_info = {
            "unique_id": variants[0].get("id") if variants else None,
            "retailer_name": "jiomart",
            "extraction_date": time.strftime("%Y-%m-%d"),
            "product_name": product.get("product", {}).get("title"),
            "brand": variants[0].get("brands", [""])[0] if variants else None,
            "url": variants[0].get("uri") if variants else None,
            "food_type" : variants[0].get("attributes", {}).get("food_type").get("text") if variants else None,
        }
        all_products.append(product_info)
         
    # ---- Extract next page token ----
    next_page_token = data.get("nextPageToken")

    if not next_page_token:
        print("No nextPageToken found, reached last page.")
        break

    # ---- Update pageToken for next request ----
    json_data["pageToken"] = next_page_token

    page += 1
    time.sleep(1)  # important to reduce rate limiting



#--------------------------------------------------------------parser---------------------------------------------------------
INPUT_JL = "/home/shahana/datahut-training/hw-training/jiomart_products.jl"
OUTPUT_JL = "/home/shahana/datahut-training/hw-training/jiomart_products_enriched.jl"

headers = {
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'cookie': 'nms_mgo_state_code=MH; WZRK_G=0c50d4f36c2346edaa505fb45de11fc1; _fbp=fb.1.1766557996359.244939257; _gcl_au=1.1.1269692634.1766557997; _gid=GA1.2.292933366.1766560675; _ALGOLIA=anonymous-354dc5e5-9a2b-4b49-b2e9-e9b4594a8c9a; nms_mgo_pincode=400054; nms_mgo_city=Mumbai; _ga=GA1.1.921928667.1766557997; AKA_A2=A; __tr_luptv=1766563384691; WZRK_S_88R-W4Z-495Z=%7B%22p%22%3A7%2C%22s%22%3A1766562611%2C%22t%22%3A1766563472%7D; _ga_XHR9Q2M3VV=GS2.1.s1766557997$o1$g1$t1766563473$j56$l0$h276523973; RT="z=1&dm=www.jiomart.com&si=28169922-12e9-42de-b3c4-81979c1a2143&ss=mjjn0lxt&sl=f&tt=oiu&obo=7&rl=1"',
    'pin': '400054',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://www.jiomart.com/p/groceries/marvel-premium-tea-1-kg/590316332',
    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}

# ---------------- PDP HTML extraction ---------------- #

def extract_pdp_data(url):
    res = requests.get(url,headers=headers)
    sel = Selector(text=res.text)

    breadcrumbs = " > ".join(
        sel.xpath('//li[@class="jm-breadcrumbs-list-item"]/a/text()').getall()
    ) or None

    specifications = {}
    rows = sel.xpath('//tr[@class="product-specifications-table-item"]')

    for row in rows:
        key = row.xpath('.//th/text()').get()
        value = row.xpath('.//td//text()').get()
        if key:
            specifications[key.strip()] = value.strip() if value else None

    description = " ".join(
        sel.xpath('//div[@id="pdp_description"]//text()').getall()
    ).strip() or None
    images=",".join(sel.xpath('//img[@class="swiper-thumb-slides-img lazyload"]/@src').getall())
    return {
        "breadcrumbs": breadcrumbs,
        "specifications": specifications,
        "product_type": specifications.get("Product Type"),
        "item_form": specifications.get("Tea Form"),
        "flavour": specifications.get("Flavor"),
        "country_of_origin": specifications.get("Country of Origin"),
        "allergens": specifications.get("Allergens Included"),
        "ingredients": specifications.get("Ingredients"),
        "description": description,
        "images":images,
    }

# ---------------- Price API extraction ---------------- #

def extract_price_data(unique_id):
    url = f"https://www.jiomart.com/catalog/productdetails/get/{unique_id}"
    res = requests.get(url, headers=headers, timeout=15)

    if res.status_code != 200:
        return {}

    data = res.json()
    print(data)
    return {
        "regular_price": data.get("data").get("mrp"),
        "selling_price": data.get("data").get("selling_price"),
        "discount_percentage": data.get("data").get("discount_pct"),
    }

# ---------------- Main pipeline ---------------- #

with open(INPUT_JL) as infile, open(OUTPUT_JL, "w") as outfile:
    for line_no, line in enumerate(infile, 1):
        line = line.strip()
        if not line:
            continue

        try:
            # Parse Python dict safely
            product = ast.literal_eval(line)
        except Exception as e:
            print(f"[SKIPPED] Line {line_no} parse error:", e)
            continue

        url = product.get("url")
        unique_id = product.get("unique_id")

        if not url or not unique_id:
            print(f"[SKIPPED] Line {line_no} missing url or unique_id")
            continue

        try:
            print(f"[{line_no}] Fetching:", url)

            pdp_data = extract_pdp_data(url)
            price_data = extract_price_data(unique_id)

            enriched_product = {
                **product,
                **pdp_data,
                **price_data,
                "pdp_fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }

            # Write VALID JSONL
            outfile.write(json.dumps(enriched_product, ensure_ascii=False) + "\n")

            time.sleep(1)  # avoid rate limiting

        except Exception as e:
            print(f"[ERROR] Line {line_no}:", e)


#----------------------------------------------------------------findings-------------------------------------------------------------------
#only beverages(tea,coffee) category
#1. The API reports a total count of 3,576 products, but only 3,476 are extracted due to a pagination
#  limit encountered at the 71st page when no next-page token is available.