import requests
from parsel import Selector
import json
import time

base_url = "https://bens-appliances.com"

# -----------------crawler----------------------
url = f"{base_url}/collections/all"
all_links = []

while url:
    response = requests.get(url)
    sel = Selector(response.text)

    # extract product URLs
    product_links = sel.xpath("//div[@class='product-item product-item--vertical   1/3--tablet-and-up 1/4--desk']/a/@href").getall()
    product_links = [base_url + link if link.startswith("/") else link for link in product_links]
    all_links.extend(product_links)

    # find next page
    next_page = sel.xpath("//a[@class='pagination__next link']/@href").get()
    if next_page:
        url = base_url + next_page if next_page.startswith("/") else next_page

#------------------parser---------------------------------
product_urls = []#list of urls

results = []

for url in product_urls:
  
    response = requests.get(url, timeout=20)
    sel = Selector(response.text)
    
    item = {
        "input_part_number": "",
        "url": url,
        "title": sel.xpath('//h1/text()').get(),
        "manufacturer": sel.xpath('//a[@class="product-meta__vendor link link--accented"]/text()').get(),
        "price": sel.xpath('//span[@class="price price--highlight"]/text()[1]').get(),
        "description": " ".join(sel.xpath('//div[@class="rte text--pull"]/p/text()').getall()),
        "oem_part_number": "",
        "retailer_part_number": "",
        "competitor_part_numbers": "",
        "compatible_products": "",
        "equivalent_part_numbers": ",".join(sel.xpath('//div[@class="col-md-4"]//text()').getall()),
        "product_specifications": "",
        "additional_description": "",
        "availability": True if sel.xpath('//button[@data-action="add-to-cart"]') else False,
        "image_urls": ",".join(sel.xpath('//div[@class="product-gallery product-gallery--with-thumbnails"]//img/@src').getall()),
        "linked_files": "",
    }

    results.append(item)
    time.sleep(1)

#---------------------findings---------------------------
#The crawler and parser is running very slowly, possibly due to API rate limits or heavy data loading.