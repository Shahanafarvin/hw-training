import requests
from parsel import Selector
import re

#----------------crawler------------------------------------------------------------------------
base_url = "https://www.beverlyhillscarclub.com/isapi_xml.php"

# Parameters
limit = 60
max_cars = 473
headers = {
    "accept": "*/*",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
    "referer": "https://www.beverlyhillscarclub.com/inventory.htm?page_no=2:60&orderby=make,year",
}

all_urls = []

for offset in range(0, max_cars, limit):
    params = {
        "module": "inventory",
        "sold": "Available",
        "future_inventory": "!1",
        "pending_sale": "!1",
        "pending": "!1",
        "limit": str(limit),
        "orderby": "make,year",
        "offset": str(offset),
    }

    response = requests.get(base_url, headers=headers, params=params)
    
    sel = Selector(response.text)
    urls = sel.xpath("//a[img[@class='img-responsive']]/@href").getall()
    all_urls.extend(urls)
    
   
#----------------------------parser------------------------------------------------------
product_urls = [
    "https://www.beverlyhillscarclub.com/1958-alfa-romeo-giulietta-spider-c-17201.htm",
    
]


for url in product_urls:
    sel = Selector(text=response.text)
    rows = sel.xpath('//table[@id="leaders"]//tr')
    car_details = {}
    for row in rows:
        key = row.xpath('./th/text()').get()
        value = row.xpath('./td/text()').get()
        if key and value:
            key = key.strip().replace(":", "")  
            value = value.strip()
            car_details[key] = value  # year,price,make,model,color are in this dictionary

    description=",".join(sel.xpath("//div[@class='description']//text()").getall())
    image_URLs=",".join(sel.xpath("//a[@class='fancybox']/@href").getall())

    script_text = sel.xpath('//script[contains(text(),"application/ld+json")]/text()').get()
    if script_text:
        match = re.search(r'"vehicleIdentificationNumber"\s*:\s*"([^"]+)"', script_text)
        if match:
            vin = match.group(1)

#--------------------------------findings------------------------------------------------
#1. Product URLs are not available in the HTML response, so the PLP API was used. However, 
# the API does not return JSON—its response contains HTML inside the API payload.

#2. VIN is not visible on the page and had to be extracted from a script tag.(re used)