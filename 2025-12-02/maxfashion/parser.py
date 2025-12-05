import json
import re
from parsel import Selector
from curl_cffi import requests
from datetime import datetime
from pymongo import MongoClient
from settings import (
    logging,
    HEADERS,
    MONGO_DB,
    MONGO_COLLECTION_PRODUCTS,
    MONGO_COLLECTION_DATA,
    MONGO_COLLECTION_URL_FAILED
)
#from items import ProductUrlItem, ProductDataItem

class Parser:
    """parser"""
    
    def __init__(self):
        self.mongo = MongoClient("localhost", 27017)
        self.db = self.mongo[MONGO_DB]
        self.api_url = 'https://www.maxfashion.com/api/catalog-browse/products/sku'
        
    def start(self):
        """Start parsing product URLs and calling API"""

        # Fetch ALL URLs from MongoDB
        cursor = self.db[MONGO_COLLECTION_PRODUCTS].aggregate([
            {"$sample": {"size": 200}}   # <-- random selection
        ])
        
        product_urls = [doc["url"] for doc in cursor if doc.get("url")]

        if not product_urls:
            logging.warning("No product URLs found in database")
            return

        logging.info(f"Found {len(product_urls)} product URLs")

        for url in product_urls:
            # Extract SKU from URL
            sku = url.rstrip("/").split("/")[-1]
            params = {"productSkus": sku}

            try:
                response = requests.get(
                    self.api_url,
                    params=params,
                    headers=HEADERS,
                    impersonate="chrome",
                )

                if response.status_code == 200:
                    self.parse_item(url, response, sku)
                else:
                    logging.error(
                        f"Failed to fetch data for SKU: {sku}, Status: {response.status_code}"
                    )
                    self.db[MONGO_COLLECTION_URL_FAILED].insert_one(
                        {"url": url, "status_code": response.status_code}
                    )

            except Exception as e:
                logging.error(f"Error fetching SKU {sku}: {str(e)}")
                self.db[MONGO_COLLECTION_URL_FAILED].insert_one(
                    {"url": url, "error": str(e)}
                )

    
    def close(self):
        """connection close"""
        self.mongo.close()

    def parse_size_color_sellingprice(self, url, sku):
        """Extract sizes, color label and sale price from product page HTML."""

        try:
            response = requests.get(url, impersonate="chrome")

        except Exception as e:
            logging.error(f"Exception for {url}: {str(e)}")
            self.db[MONGO_COLLECTION_URL_FAILED].insert_one(
                {"url": url, "error": str(e)}
            )
            return None

        selector = Selector(text=response.text)

        # Extract JSON from <script id="__NEXT_DATA__">
        product_json = selector.xpath('//script[@id="__NEXT_DATA__"]/text()').get()

        # -----------------------
        # Extract Sale Price
        # -----------------------
        sale_price = ""
        match =re.search(r'"salePrice"\s*:\s*\{.*?"amount":\s*([0-9]+)', product_json, re.S)
        if match:
            sale_price = str(match.group(1))
        # -----------------------
        # Extract Sizes
        # -----------------------
        pattern = r'"attributeName"\s*:\s*"Size".*?"allowedValues"\s*:\s*\[(.*?)\]'
        size_block = re.search(pattern, product_json, re.S)

        sizes = ""

        if size_block:
            sizes_ = re.findall(r'"value"\s*:\s*"([^"]+)"', size_block.group(1))
            if sizes_:
                sizes = sorted(set(sizes_))
        # -----------------------
        # Extract Color Label (based on SKU)
        # -----------------------
        color=""
        pattern = (
            r'"label"\s*:\s*"([^"]+)"\s*,\s*"value"\s*:\s*"'
            + re.escape(sku) +
            r'"\s*,\s*"displayOrder"\s*:'
        )

        match = re.search(pattern, product_json)

        if match:
            color = match.group(1)  

        # -----------------------
        # Build result dictionary
        # -----------------------
        return {
            "url": url,
            "sku": sku,
            "size": sizes,
            "color": color,
            "sale_price": sale_price
        }

    
    def parse_item(self, url, response, sku):
        """item part"""
        data = response.json()
    
        # EXTRACT
        product = data.get('products', [])[0]
        
        if not product:
            logging.warning(f"No product found in API response for URL: {url}")
            return
        
        # Extract basic fields
        unique_id = product.get('id', '')
        product_name = product.get('name', '')
        description = product.get('description', '')
        
        # Extract price info
        price_info = product.get('priceInfo', {})
        regular_price = price_info.get('price', {}).get('amount', '')
        currency = price_info.get('price', {}).get('currency', 'AED')
        
        # Extract image
        image_url = product.get('primaryAsset', {}).get('url', '')
        
        # Extract breadcrumbs
        breadcrumbs_list = product.get('breadcrumbs', [])
        
        # Extract attributes/details
        attributes = product.get('attributes', {})
        product_details = {}
        
        for key, attr in attributes.items():
            if isinstance(attr, dict):
                name = attr.get('nameLabel', key)
                value = attr.get('value', 'N/A')
                if name not in ["Care Instructions"]:
                    product_details[name] = value
                
        # Get extracted date
        extracted_date = datetime.now().strftime("%Y-%m-%d")
        
        #size,color,sellingprice
        result = self.parse_size_color_sellingprice( url, sku)
        size=result.get("size")
        color=result.get("color")
        selling_price=result.get("sale_price")

        # CLEAN
        product_name = product_name.strip() if product_name else ""
        description = description.strip() if description else ""
        breadcrumbs = " > ".join([crumb.get('label', '') for crumb in breadcrumbs_list])
        
        # ITEM YIELD
        item={}
        item["unique_id "] = unique_id
        item["url"] = url
        item["product_name"] = product_name
        item["product_details"] = product_details
        item["color"] = color
        item["quantity"] = ""
        item["size"] = size
        item["selling_price"] = selling_price
        item["regular_price"] = regular_price
        item["image"] = image_url
        item["description"] = description
        item["currency"] = currency
        item["breadcrumbs"] = breadcrumbs
        item["extraction_date"] = extracted_date
        
        logging.info(item)
        
        try:
            self.db[MONGO_COLLECTION_DATA].insert_one(item)
        except Exception as e:
            pass


if __name__ == "__main__":
    parser_obj = Parser()
    parser_obj.start()
    parser_obj.close()