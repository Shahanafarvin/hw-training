import requests
from parsel import Selector
from items import ProductUrlItem, ProductItem
from mongoengine import connect
from settings import HEADERS, MONGO_DB, logging
from time import sleep

class Parser:
    """Parsing Vehicle Details"""

    def __init__(self):
        connect(db=MONGO_DB, host="localhost", alias="default", port=27017)

    def start(self):
        urls = ProductUrlItem.objects() 

        for u in urls:
            url = u.url
            logging.info(f"Parsing: {url}")
            response = requests.get(url, headers=HEADERS)
            if response.status_code != 200:
                logging.warning(f"Failed to fetch {url} (status {response.status_code})")
                continue
            self.parse_item(url, response)
            sleep(0.5)

    def parse_item(self, url, response):
        sel = Selector(response.text)
        try:
            make = sel.xpath("//span[@itemprop='manufacturer']/text()").get(default="").strip()
            model = sel.xpath("//span[@itemprop='model']/text()").get(default="").strip()
            year = sel.xpath("//span[@itemprop='productionDate']/text()").get(default="").strip()
            title = sel.xpath("string((//h1[span[@itemprop='model']])[2])").get(default="").replace("\n", " ").strip()
            VIN = sel.xpath("//span[@itemprop='vehicleIdentificationNumber']/span/text()").get(default="").strip()
            price = sel.xpath("//h2[contains(@class,'stlouis-car-price')]/text()").get(default="").strip()
            mileage = " ".join(sel.xpath("//span[@itemprop='mileageFromOdometer']//text()").getall()).strip()
            transmission = sel.xpath("//span[@itemprop='vehicleTransmission']/text()").get(default="").strip()
            engine = " ".join(sel.xpath("//span[@itemprop='vehicleEngine']//text()").getall()).strip()
            color = sel.xpath("//div[@itemprop='color']/text()").get(default="").strip()
            fuel_type = ""
            body_style = ""
            description = ", ".join(sel.xpath("//span[@itemprop='description']//text()").getall()).strip()
            image_URL = ", ".join(sel.xpath("//div[@class='gallery-thumb show-car-thumbs']//a/@href").getall()).strip()

            item = ProductItem(
                source_link=url,
                make=make,
                model=model,
                year=year,
                title=title,
                VIN=VIN,
                price=price,
                mileage=mileage,
                transmission=transmission,
                engine=engine,
                color=color,
                fuel_type=fuel_type,
                body_style=body_style,
                description=description,
                image_URL=image_URL
            )
            item.save()
            logging.info(f"Saved: {title}")

        except Exception as e:
            logging.error(f"Error parsing {url}: {e}")

if __name__ == "__main__":
    parser = Parser()
    parser.start()
