import logging
import re
import json
import time
import requests
from parsel import Selector
from pymongo import MongoClient
from settings import MONGO_DB,MONGO_COLLECTION_PRODUCTS,MONGO_COLLECTION_DATA,MONGO_COLLECTION_URL_FAILED, get_headers_with_location

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class Parser:
    """Jiomart Product Enrichment Parser"""
    
    def __init__(self):
        """Initialize MongoDB connection"""
        self.mongo_client = MongoClient('mongodb://localhost:27017/')
        self.mongo = self.mongo_client[MONGO_DB]
    
    def start(self):
        """Start extraction process"""
        # Fetch all products from input collection
        products = list(self.mongo[MONGO_COLLECTION_PRODUCTS].find({}))
        total = len(products)
        logging.info(f"Found {total} products to process")
        
        for idx, product in enumerate(products, 1):
            url = product.get('url')
            unique_id = product.get('unique_id')
            
            # Get location data from product (if available)
            location = product.get('location_city')
            pincode = product.get('location_pincode')
            statecode = product.get('location_state')
            
            if not url or not unique_id:
                logging.warning(f"[{idx}/{total}] Skipping - missing url or unique_id")
                continue
            
            logging.info(f"[{idx}/{total}] Processing: {url}")
            
            try:
                # Create location-specific headers
                headers = get_headers_with_location(location, pincode, statecode, url)
                
                # Fetch and parse data
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code == 200:
                    self.parse_item(product, url, unique_id, response, headers)
                else:
                    self.mongo[MONGO_COLLECTION_URL_FAILED].insert_one({'url': url, 'status_code': response.status_code})
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                #self.mongo[MONGO_COLLECTION_URL_FAILED].insert_one({'url': url, 'error_message': e}) 
                pass
    
    
    def parse_item(self, product, url, unique_id, response, headers):
        """Parse and extract product data"""
        sel = Selector(text=response.text)
        
        # ========== XPATH DEFINITIONS ==========
        BREADCRUMBS_XPATH = '//li[@class="jm-breadcrumbs-list-item"]/a/text()'
        SPEC_ROWS_XPATH = '//tr[@class="product-specifications-table-item"]'
        DESCRIPTION_XPATH = '//div[@id="pdp_description"]//text()'
        IMAGES_XPATH = '//img[@class="swiper-thumb-slides-img lazyload"]/@data-src'
        VARIANTS_XPATH="//script[contains(text(), 'window.product_variants')]/text()"

        
        # ========== EXTRACT ==========
        breadcrumbs_list = sel.xpath(BREADCRUMBS_XPATH).getall()
        spec_rows = sel.xpath(SPEC_ROWS_XPATH)
        description_list = sel.xpath(DESCRIPTION_XPATH).getall()
        images_list = sel.xpath(IMAGES_XPATH).getall()
        variants_script=sel.xpath(VARIANTS_XPATH).get()
        
        # ========== CLEAN ==========
        breadcrumbs = " > ".join(breadcrumbs_list).strip() if breadcrumbs_list else ""
        
        specifications = {}
        for row in spec_rows:
            key = row.xpath('.//th/text()').get()
            value = row.xpath('.//td//text()').get()
            if key:
                specifications[key.strip()] = value.strip() if value else ""
        
        description = " ".join(x.strip() for x in description_list).strip() if description_list else ""
        images = ",".join(images_list) if images_list else ""
        
        if variants_script:
            json_text = re.search(r"JSON\.parse\('(.+?)'\)",variants_script,re.DOTALL).group(1)

            data = json.loads(json_text)
            variants_ = [
                v["value"]
                for facet in data
                if facet["facet_name"] == "Size"
                for v in facet["facet_values"]
            ]

            variants_string = ", ".join(variants_)
        else:
            variants_string=""


        # Extract price data
        price_data = self.parse_pricedata(unique_id, headers)
        
        # ========== BUILD ITEM ==========
        item = {}
        item["website"] = "Jiomart"
        item["url"] = url
        item["unique_id"] = unique_id
        item["product_name"] = product.get("product_name", "")
        item["extraction_date"]= product.get("extraction_date", "")
        item["brand"]= product.get("brand", "")
        item["breadcrumbs"] = breadcrumbs
        item["food_type"] = product.get("food_type")
        item["specifications"] = specifications
        item["product_type"] = specifications.get("Product Type", "")
        item["item_form"] = specifications.get("Tea Form", "")
        item["variants/flavour"] = variants_string
        item["country_of_origin"] = specifications.get("Country of Origin", "")
        item["allergens"] = specifications.get("Allergens Included", "")
        item["ingredients"] = specifications.get("Ingredients", "")
        item["description"] = description
        item["images"] = images
        item["regular_price"] = price_data.get("regular_price", "")
        item["selling_price"] = price_data.get("selling_price", "")
        item["discount_percentage"] = price_data.get("discount_percentage", "")
        item["location"] = product.get("location_city")
        item["pincode"] = product.get("location_pincode")
        item["statecode"] = product.get("location_state")
     
        
        # ========== SAVE TO MONGODB ==========
        try:
            self.mongo[MONGO_COLLECTION_DATA].insert_one(item)
            logging.info(f"Successfully saved: {item}")
        except Exception as e:
            logging.error(f"Failed to save {item.get('product_name')} | {repr(e)}")
    
    def parse_pricedata(self, unique_id, headers):
        """Extract price data from API"""
        url = f"https://www.jiomart.com/catalog/productdetails/get/{unique_id}"
        
        try:
            res = requests.get(url, headers=headers, timeout=15)
            
            if res.status_code != 200:
                logging.warning(f"Price API returned status {res.status_code}")
                return {}
            
            data = res.json()
            product_data = data.get("data", {})
            
            return {
                "regular_price": product_data.get("mrp", ""),
                "selling_price": product_data.get("selling_price", ""),
                "discount_percentage": product_data.get("discount_pct", ""),
            }
        except Exception as e:
            logging.error(f"Error fetching price data: {e}")
            return {}
    
    def close(self):
        """Close MongoDB connection"""
        self.mongo_client.close()


if __name__ == "__main__":
    parser_obj = Parser()
    parser_obj.start()
    parser_obj.close()