import re
import json
import time
import logging
import requests
from parsel import Selector
from mongoengine import connect
from settings import MONGO_DB, logging, BASE_URL,PARSER_API_URL, PARSER_HEADERS, PARSER_QUERY
from items import ProductItem, ProductDetailItem


class ProductParser:
    """Parser for saved Matalan products to extract specifications, description, size & color"""

    def __init__(self):
        connect(db=MONGO_DB, alias="default", host="localhost", port=27017)

    def start(self):
        """Loop through saved products and parse each"""
        products = ProductItem.objects()
        logging.info(f"Found {products.count()} products to parse")

        for product in products:
            url = f"{BASE_URL}/ae_en/{product.url_key}"
            logging.info(f"Processing: {url}")

            try:
                res = requests.get(url, timeout=15)
                if res.status_code != 200:
                    logging.warning(f"Failed to fetch {url}")
                    continue

                self.parse_item(res, product, url)
                time.sleep(1)  # polite delay

            except Exception as e:
                logging.error(f"Error processing {url}: {e}")

        logging.info("✓ Product parsing completed.")

    def parse_item(self, response, product, url):
        """Extract specifications, description, size & color from product page and save"""
        sel = Selector(response.text)
        script_text = sel.xpath('//script[contains(text(),"Specifications")]/text()').get()
        if not script_text:
            logging.warning(f"No script found for {url}")
            return False

        # Extract JSON inside self.__next_f.push([...])
        match = re.search(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', script_text)
        if not match:
            logging.warning(f"No JSON content found in script for {url}")
            return False

        json_str = match.group(1)
        # Decode escaped characters
        json_str = json_str.encode('utf-8').decode('unicode_escape')

        try:
            data = json.loads(json_str)
        except Exception as e:
            logging.warning(f"JSON decode error for {url}: {e}")
            return False

        specifications = {}
        description = ""

        for section in data:
            title = section.get("title")
            if title == "Specifications":
                for child in section.get("children", []):
                    specifications[child.get("label")] = child.get("value")
            elif title == "Description":
                description = section.get("value", "").strip()

        # Fetch size and color using extra API
        size, color = self.parse_size_color(product.url_key)

        # Save to ProductDetailItem
        detail_data = {
            "product_id": product.product_id,
            "name": product.name,
            "product_url": url,
            "brand_name": product.brand_name,
            "stock_status": product.stock_status,
            "price": product.price,
            "price_before_discount": product.price_before_discount,
            "currency": product.currency,
            "labeling": product.labeling,
            "image_url": product.image_url,
            "category_name" : product.category_name,
            "breadcrumbs" : product.breadcrumbs,
            "specifications": specifications,
            "product_information": description,
            "size": size,
            "color": color
        }

        try:
            detail_item = ProductDetailItem(**detail_data)
            detail_item.save()
            logging.info(f"Saved details for {product.url_key}")
        except Exception as e:
            logging.warning(f"Mongo insert failed for {product.url_key}: {e}")

        return True

    def parse_size_color(self, url_key):
        """Make an API call to fetch size and color variant options for a product"""
        variables = {"url_key": url_key}
        payload = {"query": PARSER_QUERY, "variables": json.dumps(variables), "operationName": "GetProductVarientOptions"}

        try:
            response = requests.get(PARSER_API_URL, headers=PARSER_HEADERS, params=payload, timeout=10)
            if response.status_code != 200:
                logging.warning(f"Variant API request failed for {url_key}")
                return None, None

            data = response.json()
            item = data.get("data", {}).get("products", {}).get("items", [])
            if not item:
                return None, None

            options = item[0].get("selected_variant_options", [])
            size = None
            color = None
            for opt in options:
                if opt.get("code") == "size":
                    size = opt.get("label")
                elif opt.get("code") == "color":
                    color = opt.get("label")

            return size, color

        except Exception as e:
            logging.error(f"Error fetching variant options for {url_key}: {e}")
            return None, None
    def close(self):
      """Optional cleanup method."""
      logging.info(" product crawling completed.")


if __name__ == "__main__":
    parser = ProductParser()
    parser.start()
    parser.close()
