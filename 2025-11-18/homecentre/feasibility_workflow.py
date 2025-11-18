from curl_cffi import requests
from parsel import Selector

#----------------------category key names generation----------------------------------

headers = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

url = "https://www.homecentre.com/ae"

response = requests.get(url, headers=headers, impersonate="chrome")
sel = Selector(response.text)

items = sel.xpath("(//ul[@class='row list-unstyled'])[1]/li")
for li in items[:3]:
    category_urls=li.xpath(".//ul/li/a/@href").getall()
    clean_names = []
    for u in category_urls:
        part = u.rstrip("/").split("/")[-1]        # get last segment
        part = part.split("?")[0]                  # remove query if any
        clean_names.append(part)
    print(clean_names)

#-----------------------crawler----------------------------------------------------------
import json
import time

# ----------------------------
# CONFIG
# ----------------------------
API_URL = ("https://3hwowx4270-dsn.algolia.net/1/indexes/*/queries"
           "?X-Algolia-API-Key=4c4f62629d66d4e9463ddb94b9217afb"
           "&X-Algolia-Application-Id=3HWOWX4270"
           "&X-Algolia-Agent=Algolia%20for%20vanilla%20JavaScript%202.9.7")

HEADERS = {
    "Accept": "*/*",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://www.homecentre.com",
    "Referer": "https://www.homecentre.com/",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
}

# ----------------------------
# Category names to query
# ----------------------------
category_names = [
    "furniture-bedroom",
    "furniture-sofaandseating",
]

# ----------------------------
# Function to build payload
# ----------------------------
def build_payload(category_name, page=0):
    facet_filters = [
        "inStock:1",
        "approvalStatus:1",
        f"allCategories:{category_name}",
        "badge.title.en:-LASTCHANCE"
    ]
    
    encoded_facet_filters = json.dumps(facet_filters)

    params = (
        f"query=*&hitsPerPage=42&page={page}&facets=*&facetFilters={encoded_facet_filters}"
        "&getRankingInfo=1&clickAnalytics=true"
        "&attributesToHighlight=null"
        "&attributesToRetrieve=name,url,price,thumbnailImg,gallaryImages,summary"
        "&numericFilters=price>0.9"
        "&maxValuesPerFacet=500"
    )

    payload = {
        "requests": [
            {
                "indexName": "prod_uae_homecentre_Product",
                "params": params
            }
        ]
    }

    return json.dumps(payload)

# ----------------------------
# Main scraping loop with pagination
# ----------------------------
session = requests.Session()

for name in category_names:
    print(f"\n🔎 Fetching category: {name}")

    page = 0
    total_hits = 0

    while True:
        payload = build_payload(name, page)
        response = session.post(API_URL, headers=HEADERS, data=payload)

        if response.status_code != 200:
            print(f"Error on page {page}: {response.text}")
            break

        data = response.json()
        results = data["results"][0]
        hits = results["hits"]
        nb_pages = results["nbPages"]
        for hit in hits:
             name=hit.get("name").get("ar")
             product_id=hits.get("objectID")
             urls=hit.get("url")
             details_string=hit.get("summary").get("ar")
             price=hit.get('price')
             was_price=hits.get("wasPrice")
             image=hits.get("gallaryImages")

        page += 1
        if page >= nb_pages:
            break

       
#-----------------------parser-------------------------------------------------

url = ("https://www.homecentre.com/ae/ar/%D8%A3%D8%AB%D8%A7%D8%AB/%D8%A7%D9%84%D9%83%D9%86%D8%A8-"
       "%D9%88%D8%A7%D9%84%D9%85%D9%82%D8%A7%D8%B9%D8%AF/%D9%83%D8%B1%D8%A7%D8%B3%D9%8A-"
       "%D8%A8%D8%B0%D8%B1%D8%A7%D8%B9%D9%8A%D9%86/%D9%87%D9%88%D9%85-%D8%B3%D9%86%D8%AA%D8%B1-"
       "%D9%83%D8%B1%D8%B3%D9%8A-%D9%82%D9%85%D8%A7%D8%B4---%D9%87%D9%8A%D8%B3%D8%AA%D8%B1/p/165463763")


headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

response = requests.get(url, headers=headers)
sel = Selector(response.text)
product_specs = {}

# Iterate over each attribute-group div
groups = sel.xpath("//div[contains(@class,'attribute-group-v2')]")
for group in groups:
    # Extract heading
    heading = group.xpath(".//p[contains(@class,'attribute-group-title')]/text()").get()
    if heading:
        heading = heading.strip()

    kv_pairs = {}

    # Variation 1: Horizontal key-value
    attrs_horizontal = group.xpath(".//div[contains(@class,'attribute-group-desc-horizontal1')]//div[contains(@class,'attribute-v2')]")
    for attr in attrs_horizontal:
        key = attr.xpath(".//p[contains(@class,'attribute-v2-name')]/text()").get()
        value = attr.xpath(".//p[contains(@class,'attribute-v2-value')]/text()").get()
        if key and value:
            kv_pairs[key.strip()] = value.strip()

    # Variation 2: Table-style key-value
    attrs_table = group.xpath(".//div[contains(@class,'attribute-group-desc-table')]//div[contains(@class,'row')]")
    for row in attrs_table:
        key = row.xpath(".//div[contains(@class,'attribute-table-key')]/text()").get()
        value = row.xpath(".//div[contains(@class,'attribute-table-value')]/text()").get()
        if key and value:
            kv_pairs[key.strip()] = value.strip()

    if heading and kv_pairs:
        product_specs[heading] = kv_pairs

quantity=product_specs.get("الوزن والأبعاد")
material=product_specs.get("الخامة")
specifications=product_specs.get("المواصفات العامة")
color=sel.xpath("//strong[@id='product-title-01']//text()").get()
breadcrumbs=" > ".join(sel.xpath("//ol[@id='breadcrumb']/li//text()").getall())
stock=sel.xpath("//strong[@id='product-stock']//text()").get()


#------------------------findings-----------------------------------------------------
#1. The PLP page HTML response has no <a> tags, indicating JavaScript-rendered content; therefore, API calls were used. Category keywords need to be generated from the homepage HTML response for the API calls.

#2. The homepage HTML response shows unusual behavior: despite a 404 status code, the response content is correct.