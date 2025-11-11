from curl_cffi import requests
from parsel import Selector
import json

#---------------------crawler----------------------
url = "https://www.gatewayclassiccars.com/cars?max_year=1990&min_year=1914"
while url:
   
    response = requests.get(url, impersonate="chrome110", timeout=5)
    sel = Selector(response.text)

    # extract product URLs
    for link in sel.xpath("//div[@class='col-12 col-md-5 px-3']//a[starts-with(@href, 'https://www.gatewayclassiccars.com/vehicle')]/@href").getall():
        print(link)
    # find next page
    next_page = sel.xpath("//a[@rel='next']/@href").get()
    if next_page:
        url = next_page
        
#-----------------parser---------------------------------------
urls = [
    "https://www.gatewayclassiccars.com/vehicle/dfw/2999/1957-chevrolet-bel-air",
    "https://www.gatewayclassiccars.com/vehicle/stl/9955/1970-chevrolet-nova",
]

for url in urls:
    response = requests.get(url, impersonate="chrome110", timeout=5)
    sel = Selector(text=response.text)
    
    source_link = url
    description = " ".join(sel.xpath("//div[@class='card-body']//text()").getall())
    # Extract JSON-LD Car data
    scripts = sel.xpath("//script[@type='application/ld+json']/text()").getall()
  
    car_json_objects = []

    for script_content in scripts:
        
        script_content = script_content.strip()
        if '"type": "car"' in script_content:
            try:
                data = json.loads(script_content)
            except json.JSONDecodeError:
                continue

            vin = data.get("vehicleIdentificationNumber")
            year = data.get("vehicleModelDate")
            model = data.get("model")
            make = data.get("brand", {}).get("name")
            price = data.get("offers", {}).get("price")
            mileage = data.get("mileageFromOdometer", {}).get("value")
            transmission = data.get("vehicleTransmission")
            engine = data.get("vehicleEngine", {}).get("name")
            color = data.get("color")
            body_style = data.get("bodyType")
            image_url = data.get("image")

#------------findings-----------------------------
#1. Higher load times were detected; performance improved using curl_cffi.