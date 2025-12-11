import requests
from parsel import Selector

#-------------------------------------------input based searching results in plp page----crawler----------------------------------------

inputs = ["3282770149715", "5414963013512", "3401360212237"] #sample inputs

for q in inputs:

    url = f"https://www.farmaline.be/nl/search.htm?eventName=search-submit&i=1&q={q}&searchChannel=algolia&userToken=anonymous-c7c04c9d-675e-4683-b334-d275d0691c0b"
    

    response = requests.get(url)
    print("Status:", response.status_code)

    sel = Selector(response.text)
    products = sel.xpath("//li[@data-qa-id='result-list-entry']")
    

    for product in products:
        product_url = product.xpath(".//a[@data-qa-id='serp-result-item-title']/@href").get()
        name = product.xpath(".//a[@data-qa-id='serp-result-item-title']//text()").get()
        selling_price = product.xpath(".//span[@data-qa-id='entry-price']/text()").get()
        discount = product.xpath(".//div[@class='flex min-w-12 items-center justify-center p-1 text-dark-primary-max rounded-full bg-light-tertiary font-mono text-xs font-medium']/span/text()").get()
        regular_price = product.xpath(".//div[@class='text-dark-primary-max']/span[@class='line-through']/text()").get()

#------------------------------------------parser (if requirements fields changes)----------------------------------------------------------

import requests
from parsel import Selector

url = "https://www.farmaline.be/nl/schoonheid/BE03720083/ducray-kelual-emulsie-nieuwe-formule.htm?eventName=click+on+product+list+item&position=1&query=3282770202274&queryID=15c236670f9deed801c8cf9bf451883b&eventType=click&objectIDs=%5BBE03720083%5D"
response=requests.get(url)

sel=Selector(response.text)
breadcrumbs=" > ".join(sel.xpath("//span[@class='hidden items-center gap-2 whitespace-nowrap first:flex mobile-sm:last:flex desktop:flex desktop:last:hidden']//text()").getall())
product_name=sel.xpath("//h1[@data-qa-id='product-title']/text()").get()
reviews=sel.xpath("//a[@data-qa-id='number-of-ratings-text']/text()").get()
package_size=sel.xpath("//div[@data-qa-id='product-attribute-package_size']//text()").get()
price_per_size=sel.xpath("//div[@class='text-xs text-dark-primary-strong']//text()").get()
details = {}

items = sel.xpath("//li[contains(@class,'flex grow flex-row items-start text-s text-dark-primary-max')]")

for item in items:
    key = item.xpath(".//dt//text()").get()
    value = item.xpath(".//dd//text()").get()

    if key and value:
        details[key.strip()] = value.strip()

product_description=sel.xpath("//div[@data-qa-id='product-description']//text()").getall()
rating=sel.xpath("//div[@data-qa-id='product-ratings-container']//span[@class='mb-2.5 text-4xl']//text()").get()
images=",".join(sel.xpath("//button[contains(@class,'w-1/3')]//picture//img/@src").getall())


#---------------------------------------------findings----------------------------------------------------------
#1. According to the current inputs, most of inputs return an exact match when searched using EAN MASTER and CNK BELUX.

#2. If both EAN MASTER and CNK BELUX return no results, then searching with PRODUCT GENERAL NAME return matches, 
# but name-based matching is unpredictable.

#3. A single input may return multiple products.

#4. Name and price details can be extracted directly from PLP pages without additional parser requests. 
# If field requirements change, PDP requests may be needed.