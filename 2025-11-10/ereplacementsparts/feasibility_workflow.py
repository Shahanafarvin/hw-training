import requests
from parsel import Selector

HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Origin": "https://www.ereplacementparts.com",
    "Pragma": "no-cache",
    "Priority": "u=1, i",
    "Referer": "https://www.ereplacementparts.com/",
    "Sec-CH-UA": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Linux"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
}

#----------------category url extraction---------------------
BASE_URL = "https://www.ereplacementparts.com/accessories-c-714.html"
response = requests.get(BASE_URL, headers=HEADERS)
sel = Selector(response.text)
data = []

# Adjust these XPaths or CSS selectors based on site structure
for cat in sel.xpath("//div[@class='product_listing']"):
    category_name = cat.xpath(".//div[@class='product_name']//a/text()").get().strip()
    category_url = cat.xpath(".//div[@class='product_name']//a/@href").get()

    subcategories = []
    for sub in cat.xpath(".//div[@class='subcategory-link']"):
        sub_name = sub.xpath(".//a/span/text()").get().strip()
        sub_url = sub.xpath(".//a/@href").get()
        if sub_name and sub_url:
            subcategories.append({"name": sub_name, "url": sub_url})

    data.append({
        "category": category_name,
        "url": category_url,
        "subcategories": subcategories
    })

#-----------------------------crawler------------------------------------
all_links = []
next_page = subcategory_url

while next_page:
    resp = requests.get(next_page, headers=HEADERS)
    sel = Selector(resp.text)
    products = sel.xpath("//a[@class='imglink']/@href").getall()
    for link in products:
        all_links.append(link)

    # Find next page from pagination div
    next_page = sel.xpath(
        "//div[@class='pagination-arrows']//a[img/@alt='next page']/@href"
    ).get()

#----------------------parser-------------------------------------------------
r = requests.get(product_url, headers=HEADERS)
sel = Selector(r.text)

breadcrumbs = sel.xpath("//div[@class='crumbs d-flex align-items-center']//span[@itemprop='name' or @class='mach-breadcrumb']/text()").getall()
name = sel.xpath("//h1/text()").get().strip()
oem_part_for=sel.xpath("//span[@itemprop='brand']/text()").get().strip()
part_number=sel.xpath("//span[@itemprop='mpn']/text()").get().strip()
price = sel.xpath("//span[@itemprop='price']/text()").get().strip()
availability=sel.xpath("//span[@temprop='availability']/text()").get()
description = " ".join(sel.xpath("//div[@id='primary_desc']//text()").getall()).strip()
additional_description = " ".join(sel.xpath("//ul[@id='add_desc']//text()").getall()).strip()

