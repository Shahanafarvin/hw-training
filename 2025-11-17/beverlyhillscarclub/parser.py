import re
import requests
from parsel import Selector
from mongoengine import connect
from items import PeoductURLItem, ProductDataItem
from settings import MONGO_DB, HEADERS, logging


class Parser:
    def __init__(self):
        connect(db=MONGO_DB, host="localhost", alias="default", port=27017)

    def start(self):
        urls = PeoductURLItem.objects()

        logging.info(f"Parser started… Total URLs: {len(urls)}")

        for entry in urls:
            url = entry.url
            self.parse_item(url)
   
    def parse_item(self, url):
        logging.info(f"Parsing → {url}")

        response = requests.get(url, headers=HEADERS)
        sel = Selector(response.text)

        # ---------- Extract Table Details ----------
        car_details = {}
        for row in sel.xpath('//table[@id="leaders"]//tr'):
            key = row.xpath('./th//text()').get()
            val = row.xpath('./td//text()').get()
            if key and val:
                key = key.strip().replace(":", "")
                val = val.strip()
                car_details[key] = val

        # ---------- Year Condition ----------
        year = float(car_details.get("Year", "0"))
        if year > 1990:
            logging.info(f"Skipping {url} — year {year} > 1990")
            return None  # stop parsing this item

        # ---------- Basic Fields ----------
        make = car_details.get("Make")
        model = car_details.get("Model")
        price = car_details.get("Price") or car_details.get("Sale")
        color = car_details.get("Color")

        # ---------- Description ----------
        desc_list = sel.xpath("//div[@class='description']//text()").getall()
        description = ",".join(x.strip() for x in desc_list if x.strip())

        # ---------- Image URLs ----------
        image_urls = sel.xpath("//a[@class='fancybox']/@href").getall()

        # ---------- VIN Extraction ----------
        script_text = sel.xpath(
            '//script[contains(text(),"application/ld+json")]/text()'
        ).get()

        vin = None
        if script_text:
            m = re.search(r'"vehicleIdentificationNumber"\s*:\s*"([^"]+)"', script_text)
            if m:
                vin = m.group(1)

        # ---------- Save Item ----------
        item = ProductDataItem(
            source_link=url,
            make=make,
            model=model,
            year=year,
            VIN=vin,
            price=price,
            color=color,
            description=description,
            image_URLs=image_urls,
        )

        item.save()
        logging.info(f"Saved → {url}")
        return item


# ---------------------------------------------------------
if __name__ == "__main__":
    parser = Parser()
    parser.start()
