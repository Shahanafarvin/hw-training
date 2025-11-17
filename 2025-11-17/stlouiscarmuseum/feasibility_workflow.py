import requests
from parsel import Selector

headers = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "origin": "https://www.stlouiscarmuseum.com",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
}

#----------------------crawler--------------------------------

BASE = "https://www.stlouiscarmuseum.com"
url = f"{BASE}/vehicles"
all_urls = []

while url:
    response = requests.get(url, headers=headers)
    sel = Selector(response.text)

    links = sel.xpath("//a[@class='stlouis-list-item']/@href").getall()
    for link in links:
        if link.startswith("/"):
            full_url = BASE + link
        else:
            full_url = link
        all_urls.append(full_url)

    # pagination ---- <a rel="next">
    next_page = sel.xpath("//a[@rel='next']/@href").get()

    if next_page:
        if next_page.startswith("/"):
            url = BASE + next_page
        else:
            url = next_page
    else:
        url = None

#---------------------parser---------------------------------

# your list from previous scraping
urls = ['https://www.stlouiscarmuseum.com/vehicles/1218/1965-ford-mustang', 'https://www.stlouiscarmuseum.com/vehicles/1219/1984-ford-shay-motors-model-a-roadster-pickup', 'https://www.stlouiscarmuseum.com/vehicles/1217/1972-datsun-240z']


for url in urls:
    response = requests.get(url,headers=headers)
    status = response.status_code
    
    if status == 200:
        
        sel = Selector(response.text)
        make=sel.xpath("//span[@itemprop='manufacturer']/text()").get().strip()
        model=sel.xpath("//span[@itemprop='model']/text()").get().strip()
        year=sel.xpath("//span[@itemprop='productionDate']/text()").get().strip()
        title = sel.xpath("string((//h1[span[@itemprop='model']])[2])").get().replace("\n\n"," ").replace("\n","").strip()
        VIN=sel.xpath("//span[@itemprop='vehicleIdentificationNumber']/span/text()").get().strip()
        price=sel.xpath("//h2[@class='stlouis-car-price']/text()").get().strip()
        mileage=sel.xpath("//span[@itemprop='mileageFromOdometer']//text()").getall()
        transmission=sel.xpath("//span[@itemprop='vehicleTransmission']/text()").get().strip()
        engine=sel.xpath("//span[@itemprop='vehicleEngine']//text()").getall()
        color=sel.xpath("//div[@itemprop='color']/text()").get().strip()
        fuel_type=""
        body_style=""
        description=",".join(sel.xpath("//span[@itemprop='description']//text()").getall())
        image_URL=",".join(sel.xpath("//div[@class='gallery-thumb show-car-thumbs']//a/@href").getall())
        #source_link=url
        

#----------------finfings------------------------------------
#1. 403 Forbidden error is detected when requests are made without proper headers.