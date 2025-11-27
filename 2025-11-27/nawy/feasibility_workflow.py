import requests
import json
import time

#--------------------------------------crawler.py--------------------------------------#    
url = "https://webapi.nawy.com/api/properties/search?token=undefined&language=en&client_id=LObZQx8rno"

headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en",
    "cache-control": "no-cache",
    "client-id": "LObZQx8rno",
    "content-type": "application/json",
    "origin": "https://www.nawy.com",
    "platform": "web",
    "pragma": "no-cache",
    "referer": "https://www.nawy.com/",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
}

total_collected = 0
start = 1
page_number = 1

while True:  # Loop indefinitely, break based on conditions after saving
    payload = {"show": "property", "start": start}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    data = response.json()
    total_properties = data.get("total_properties", 0)
    properties = data.get("values", [])

    print(f"Page {page_number}, start={start} → got {len(properties)} items")

    page_data = []

    for item in properties:
        extracted = {
            "id": item.get("id"),
            "compound_slug": item.get("compound", {}).get("slug"),
            "property_slug": item.get("slug"),
            "url": f"https://www.nawy.com/en/property/{item.get('compound', {}).get('slug')}/property/{item.get('slug')}",
            "broker_display_name": item.get("developer", {}).get("name"),
            "currency": item.get("currency"),
            "price": item.get("max_price"),
            "title": item.get("name"),
            "bathrooms": item.get("number_of_bathrooms"),
            "bedrooms": item.get("number_of_bedrooms"),
            "property_type": item.get("property_type", {}).get("name")
        }
        page_data.append(extracted)

    total_collected += len(page_data)
    start += len(properties)
    page_number += 1

    time.sleep(1)

    # Now check the total_collected condition after saving
    if total_collected >= total_properties:
        print(f"Reached the expected total: {total_collected} ≥ {total_properties}. Stopping pagination.")
        break


#--------------------------------------parser.py--------------------------------------#
import requests
from parsel import Selector

url="https://www.nawy.com/compound/181-il-bosco-new-capital/property/104409-apartment-for-sale-in-il-bosco-new-capital-with-1-bedroom-in-new-capital-city-by-misr-italia-properties"

response = requests.get(url)
print(response.status_code)
sel= Selector(response.text)
location= sel.xpath("//h2[@itemprop='address']//text()").get()
description=" ".join(sel.xpath("//div[@data-cy='description-container']//text()").getall())
amenities= ",".join(sel.xpath("//div[@itemprop='amenityFeature']//text()").getall())
number_of_photos= len(sel.xpath("//div[@class='imageContainer']/div").getall())
details=",".join(sel.xpath("//div[@class='sc-32ba891c-0 bfaAYI']//text()").getall())

#------------------------------------------findings------------------------------------------#
#1. The PLP page uses infinite scrolling, so pagination is handled through the PLP API call.

#2. URLs need to be generated manually because they are not provided explicitly.

#3. The ID is taken as the reference number since no explicit product ID is provided, and the same value appears in the URL.