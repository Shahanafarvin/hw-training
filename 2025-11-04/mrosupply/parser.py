import logging
import time
import requests
from parsel import Selector
from mongoengine import connect, disconnect
from settings import MONGO_DB,logging
import json
from items import ProductUrlItem, ProductDetailItem


class Parser:
    """MRO Supply parser using URLs from MongoDB"""

    def __init__(self):
        """Initialize Mongo connection"""
        connect(db=MONGO_DB, alias='default', host='localhost', port=27017)

    def start(self):
        """Main runner: fetch URLs from collection and parse"""
        all_categories = ProductUrlItem.objects()
        total_urls = sum(len(cat.product_urls) for cat in all_categories)
        logging.info(f" Total product URLs found: {total_urls}")

        for category in all_categories:
            for url in category.product_urls:
                try:
                    response = requests.get(url, timeout=20)
                    if response.status_code == 200:
                        self.parse_item(url, response)
                        time.sleep(1)
                    else:
                        logging.warning(f" Failed request {url}: {response.status_code}")
                except Exception as e:
                    logging.error(f" Request error for {url}: {e}")

        logging.info(" Completed parsing all products.")

    def close(self):
        """Close Mongo connection"""
        disconnect()

    def parse_item(self, url, response):
        """Parse product details and save to ProductDetailItem"""
        sel = Selector(text=response.text)
        item_data = {}

        # Extract JSON-LD data
        json_text = sel.xpath('//script[@type="application/ld+json"]/text()').get()
        if json_text:
            try:
                jd = json.loads(json_text)
                item_data["Item_Name"] = jd.get("name")
                item_data["Product_Category"] = jd.get("category")

                if jd.get("brand"):
                    item_data["Brand_Name"] = jd["brand"].get("name")
                    item_data["Manufacturer_Name"] = jd["brand"].get("name")
                offers = jd.get("offers")
                offer = offers[0] if isinstance(offers, list) else offers
                if offer:
                    item_data["Price"] = offer.get("price")
                    item_data["Availability"] = (
                        offer.get("availability").split("/")[-1]
                        if offer.get("availability")
                        else None
                    )
                    seller = offer.get("seller")
                    if seller:
                        item_data["Vendor_Seller_Part_Number"] = offer.get("sku")
                    item_data["Manufacturer_Part_Number"] = offer.get("mpn")
                item_data["QTY_Per_UOI"] = jd.get("weight")
            except Exception:
                logging.warning(f"JSON decode failed for {url}")

        # Description table
        description = {}
        if sel.xpath('//table[@class="description-table"]//tr'):
            for row in sel.xpath('//table[@class="description-table"]//tr'):
                key = row.xpath(".//th/text()").get()
                val = row.xpath(".//td/text()").get()
                if key and val:
                    description[key.strip()] = val.strip()
            item_data["Full_Product_Description"] = ", ".join(
                f"{k}: {v}" for k, v in description.items()
            )
        else:
            item_data["Full_Product_Description"] = " ".join(
                sel.xpath('//div[@id="additionalDescription"]/div/p//text()').getall()
            ).strip()


        for div in sel.xpath("//div[@class='flex-table--item']"):
            headtext=div.xpath("./div[@class='flex-table--head']/p/text()").get()
           
            if headtext == "UOM":
                item_data["Unit_of_issue"]=div.xpath("./div[@class='flex-table--body']/p/text()").get()
            if headtext == "UPC":
                item_data["Upc"]=div.xpath("./div[@class='flex-table--body']/p/text()").get()
        

        item_data["Model_Number"] = item_data.get("Manufacturer_Part_Number")
        item_data["Company_Name"] = "MRO Supply"
        item_data["URL"] = url
        
        
        try:
            product_item = ProductDetailItem(**item_data)
            product_item.save()
            logging.info(f"Saved: {url}")
        except Exception as e:
            logging.error(f"MongoEngine save failed for {url}: {e}")


if __name__ == "__main__":
    parser_obj = Parser()
    parser_obj.start()
    parser_obj.close()
