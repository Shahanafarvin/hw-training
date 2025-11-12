import json
import time
from mongoengine import connect
from parsel import Selector
from curl_cffi import requests
from settings import MONGO_DB, logging
from items import ProductItem, ProductUrlItem



class Parser:
    """Parsing vehicle details from Gateway Classic Cars"""

    def __init__(self):
        connect(db=MONGO_DB, alias='default', host='localhost', port=27017)

    def start(self):
        """Start parser"""
        # Fetch all URLs from the crawler collection
        urls = ProductUrlItem.objects.only("url")
        logging.info(f"Found {urls.count()} URLs to parse.")

        for url_doc in urls:
            url = url_doc.url
            try:
                response = requests.get(url, impersonate="chrome110", timeout=10)
                if response.status_code == 200:
                    self.parse_item(url, response)
                    time.sleep(1)
                else:
                    logging.warning(f"Failed to fetch {url}")
            except Exception as e:
                logging.warning(f"Request error for {url}: {e}")

    def parse_item(self, url, response):
        """Extract car data"""
        sel = Selector(response.text)

        source_link = url
        description = " ".join(sel.xpath("//div[@class='card-body']//text()").getall())
        # Extract JSON-LD Car data
        scripts = sel.xpath("//script[@type='application/ld+json']/text()").getall()

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


        item = {
            
            "source_link": source_link,
            "make": make,
            "model": model,
            "year": year,
            "VIN": vin,
            "price": price,
            "description": description,
            "mileage": mileage,
            "transmission": transmission,
            "engine": engine,
            "color": color,
            "body_style": body_style,
            "image_url": image_url,
        }

        try:
            product_item = ProductItem(**item)
            product_item.save()
            logging.info(f"product inserted : {url}")
        except Exception as e:
            logging.warning(f"Mongo insert failed: {e}")

    def close(self):
        """Close function for cleanup"""
        logging("scraping completed")

if __name__ == "__main__":
    parser = Parser()
    parser.start()
    parser.close()
