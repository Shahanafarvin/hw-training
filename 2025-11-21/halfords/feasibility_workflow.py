import requests
from parsel import Selector
import json
import os

#--------------------category url extraction------------------------------------------
url="https://www.halfords.com/"
response = requests.get(url)
print(response.status_code)
sel = Selector(response.text)
categories = {}
category_tags = sel.xpath("//li[@class='mm-list-list-item mm-list-list-item1  ']")
                
for li in category_tags:

    # Category Name & URL
    name = li.xpath("./a//text()").get()
    link = li.xpath("./a/@href").get()
    if not link:
        continue
    full_link = f"https://www.halfords.com{link}"

    categories[name] = {
        "url": full_link,
        "subcategories": {}
    }


    # SUB-CATEGORIES
    subcategory_tags = li.xpath(".//li[@class='mm-list-list-item mm-list-list-item2  ']")

    for sub_li in subcategory_tags:

        sub_name = sub_li.xpath("./a//text()").get()
        sub_link = sub_li.xpath("./a/@href").get()
        if not sub_link:
            continue
        full_sublink = f"https://www.halfords.com{sub_link}"

        categories[name]["subcategories"][sub_name] = {
            "url": full_sublink,
            "sub_subcategories": {}
        }

        
        # SUB-SUB-CATEGORIES
        sub_subcategory_tags = sub_li.xpath(".//li[@class='mm-list-list-item mm-list-list-item3  ']")

        for sub_subli in sub_subcategory_tags:

            sub_sub_name = sub_subli.xpath("./a//text()").get()
            sub_sub_link = sub_subli.xpath("./a/@href").get()
            if not sub_sub_link:
                continue
            full_sub_sublink = f"https://www.halfords.com{sub_sub_link}"

            categories[name]["subcategories"][sub_name]["sub_subcategories"][sub_sub_name] = {
                "url": full_sub_sublink
            }

#----------------------------------crawler---------------------------------------------------
all_products = {}

for cat, cat_data in categories.items():

    all_products[cat] = {}

    for sub, sub_data in cat_data.get("subcategories", {}).items():
        print(f"\n  → Subcategory: {sub}")

        all_products[cat][sub] = {}

        for subsub, subsub_data in sub_data.get("sub_subcategories", {}).items():
            print(f"     → Sub-Subcategory: {subsub}")

            url = subsub_data["url"]
            print(f"        URL: {url}")

            response = requests.get(url)
            print("        Status:", response.status_code)
            sel = Selector(response.text)

            # -------------------------------------------
            # CHECK DEEPER SUB-CATEGORIES
            # -------------------------------------------
            more_subcats = sel.xpath("//li[@class='border-bottom border-gray-200']/a/@href").getall()

            final_product_links = []

            # -------------------------------------------
            # FUNCTION: PAGINATION (Load More)
            # -------------------------------------------
            def collect_all_products_from_page(start_url):
                page_url = start_url

                while True:
                    print(f"        → Fetching page: {page_url}")
                    r = requests.get(page_url)
                    print("          Status:", r.status_code)
                    s = Selector(r.text)

                    # Extract product links on this page
                    links = s.xpath("//a[@data-action-name='plp.product.click']/@href").getall()
                    print(f"          Found {len(links)} products on this page.")
                    final_product_links.extend(links)

                    # Check for load more button
                    next_page = s.xpath("//a[@data-cmp-id='loadMore']/@href").get()

                    if next_page:
                        print(f"          Load More found → Next page: {next_page}")
                        page_url = next_page
                    else:
                        print("          No more pages.")
                        break

            # -------------------------------------------
            # CASE 1: DEEPER SUBCATEGORIES EXIST
            # -------------------------------------------
            if more_subcats:
                print(f"        Found {len(more_subcats)} deeper categories.")
                more_subcats = [
                    f"https://www.halfords.com{link}" if link.startswith("/") else link
                    for link in more_subcats
                
                ]
                for child_url in more_subcats:
                    print(f"        Visiting deeper: {child_url}")

                    collect_all_products_from_page(child_url)

            # -------------------------------------------
            # CASE 2: NO DEEPER CATEGORIES → DIRECT PAGINATION
            # -------------------------------------------
            else:
                print("        No deeper categories → Using pagination directly.")
                collect_all_products_from_page(url)


            all_products[cat][sub][subsub] = final_product_links

#----------------------------------parser------------------------------------------------------

url="https://www.halfords.com/motoring/batteries/car-batteries/yuasa-ybx7335-12v-80ah-780a-efb-start%2Fstop-battery-485454.html"

response = requests.get(url)
print(response.status_code)

sel = Selector(response.text)

script_tags = sel.xpath("//script[@type='application/ld+json']/text()").getall()
for script in script_tags:
    data = json.loads(script)
    if "BreadcrumbList" in data.get("@type", ""):
        
        breadcrumbs=[]
        breadcrumb_list=data.get("itemListElement", [])
        for item in breadcrumb_list:
            breadcrumb = item.get("name")
            breadcrumbs.append(breadcrumb)

    if "Product" in data.get("@type", ""):
        #print(data)
        product_name = data.get("name")
        sku = data.get("sku")
        rating=data.get("aggregateRating", {}).get("ratingValue")
        reviews=data.get("aggregateRating", {}).get("reviewCount")
        currency = data.get("offers", {}).get("priceCurrency")
        price = data.get("offers", {}).get("price")
        priceValidUntil = data.get("offers", {}).get("priceValidUntil")
        availability = data.get("offers", {}).get("availability", "").split("/")[-1]
        seller = data.get("offers", {}).get("seller", {}).get("name")
        mpn = data.get("mpn")
        image = data.get("image")

            
product_script=sel.xpath("//script[@class='js-model' and @type='application/json']/text()").get()
product_data=json.loads(product_script)

product=product_data.get("product", {})
selling_price=product.get("price", {}).get("sales",{}).get("decimalPrice","")
regular_price=product.get("price", {}).get("list",{}).get("decimalPrice","") if product.get("price", {}).get("list",{}) else ""
label=product.get("price", {}).get("saveLabel","")

feature_html =product.get("plp3", "")
fsel=Selector(feature_html)
features = ",".join(fsel.xpath("//li/text()").getall())

tabs = product.get("tabs",{}).get("list",[])

description = ""
specification = {}

for tab in tabs:

    # -------------------------
    # EXTRACT DESCRIPTION TAB
    # -------------------------
    if tab["tabLabel"] == "Description":
        html = tab["tabMarkup"]
        sel = Selector(html)
        description = sel.xpath("string(.)").get().strip()

    # -------------------------
    # EXTRACT SPECIFICATION TAB
    # -------------------------
    if tab["tabLabel"] == "Specification":
        html = tab["tabMarkup"]
        sel = Selector(html)

        rows = sel.xpath("//table//tr")
        for row in rows:
            key = row.xpath("./td[1]//text()").getall()
            key = " ".join([k.strip() for k in key if k.strip()])  # remove empty strings

            # Extract and clean value
            value = row.xpath("./td[2]//text()").getall()
            value = " ".join([v.strip() for v in value if v.strip()])

            if key and value:
                specification[key] = value

#---------------------------------findings-----------------------------------------------
#1. The crawler requires significantly more time and a high number of requests because each category contains multiple nested subcategories that must be crawled repeatedly.





           

