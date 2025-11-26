import json
import re
import requests
from parsel import Selector
from mongoengine import connect
from items import ProductUrlItem, ProductDataItem
from settings import logging, MONGO_DB, MONGO_HOST, MONGO_PORT


class Parser:
    """Parser for Halfords product data"""
    
    def __init__(self):
        self.mongo = connect(db=MONGO_DB, host=MONGO_HOST, alias="default", port=MONGO_PORT)
    
    def start(self):
        """Start code"""
        # Fetch URLs from MongoDB
        url_docs = ProductUrlItem.objects()
        
        if not url_docs:
            logging.error("No URLs found in database")
            return
        
        logging.info(f"Found {url_docs.count()} URLs to process")
        
        for url_doc in url_docs:
            url = url_doc.url
            
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    self.parse_item(url, response)
                else:
                    logging.warning(f"Status code {response.status_code} for {url}")
            except Exception as e:
                logging.error(f"Error fetching {url}: {str(e)}")
    
    def close(self):
        """Connection close"""
        self.mongo.close()
    
    def parse_item(self, url, response):
        """Item part"""
        sel = Selector(text=response.text)
        
        #XPATH
        SCRIPTTAGS_XPATH = "//script[@type='application/ld+json']/text()"
        JSMODEL_XPATH = "//script[@class='js-model' and @type='application/json']/text()"
    
        # Extract data from LD+JSON scripts
        script_tags = sel.xpath(SCRIPTTAGS_XPATH).getall()

        breadcrumbs = []

        for script in script_tags:
            try:
                data = json.loads(script)
                
                # Extract Breadcrumbs
                if "BreadcrumbList" in data.get("@type", ""):
                    breadcrumb_list = data.get("itemListElement", [])
                    for item in breadcrumb_list:
                        breadcrumb = item.get("name")
                        if breadcrumb:
                            breadcrumbs.append(breadcrumb)
                
                # Extract Product data
                if "Product" in data.get("@type", ""):
                    product_name = data.get("name", "")
                    sku = data.get("sku", "")
                    rating = data.get("aggregateRating", {}).get("ratingValue", "")
                    reviews = data.get("aggregateRating", {}).get("reviewCount", "")
                    currency = data.get("offers", {}).get("priceCurrency", "")
                    price = data.get("offers", {}).get("price", "")
                    priceValidUntil = data.get("offers", {}).get("priceValidUntil", "")
                    availability = data.get("offers", {}).get("availability", "").split("/")[-1]
                    seller = data.get("offers", {}).get("seller", {}).get("name", "")
                    mpn = data.get("mpn", "")
                    image = data.get("image", "")
            
            except json.JSONDecodeError as e:
                logging.error(f"Error parsing JSON: {str(e)}")
                continue
        
        # Extract product data from js-model script
        try:
            product_script = sel.xpath(JSMODEL_XPATH).get()

            specification={}

            if product_script:
                product_data = json.loads(product_script)
                product = product_data.get("product", {})
                product_name = product.get("productName", product_name)
                selling_price = product.get("price", {}).get("sales", {}).get("decimalPrice",price)
                regular_price = product.get("price", {}).get("list", {}).get("decimalPrice", "") if product.get("price", {}).get("list", {}) else ""
                label = product.get("price", {}).get("saveLabel", "")
                
                # Extract features
                feature_html = product.get("plp3", "")
                if feature_html:
                    fsel = Selector(feature_html)
                    features = ",".join(fsel.xpath("//li/text()").getall())
                else:
                    features = ""
                
                # Extract tabs (Description & Specification)
                tabs = product.get("tabs", {}).get("list", [])
                
                for tab in tabs:
                    # Extract Description
                    if tab.get("tabLabel") == "Description":
                        html = tab.get("tabMarkup", "")
                        # Remove <style>...</style> blocks AND stray CSS comments
                        clean = re.sub(r"<style.*?>.*?</style>", "", html, flags=re.DOTALL|re.IGNORECASE)
                        clean = re.sub(r"/\*.*?\*/", "", clean, flags=re.DOTALL)   # remove CSS comments

                        # Also remove HTML comments if any
                        clean = re.sub(r"<!--.*?-->", "", clean, flags=re.DOTALL)
                        # Clean non-breaking spaces
                        clean = clean.replace("\xa0", " ")
                        # Strip leading whitespace
                        clean = clean.strip()

                        # Now extract readable text
                        sel = Selector(clean)
                                
                        lines = [
                            t.strip()
                            for t in sel.xpath("//text()").getall()
                            if t.strip()
                        ]

                        # Remove duplicates, keep order
                        clean_lines = []
                        seen = set()

                        for line in lines:
                            if line not in seen:
                                clean_lines.append(line)
                                seen.add(line)

                        description = ",".join(clean_lines)
                    
                    # Extract Specification
                    if tab.get("tabLabel") == "Specification":
                        html = tab.get("tabMarkup", "")
                        spec_sel = Selector(html)
                        rows = spec_sel.xpath("//table//tr")
                        
                        for row in rows:
                            key = row.xpath("./td[1]//text()").getall()
                            key = " ".join([k.strip() for k in key if k.strip()])
                            
                            value = row.xpath("./td[2]//text()").getall()
                            value = " ".join([v.strip() for v in value if v.strip()])
                            
                            if key and value:
                                specification[key] = value
        
        except (json.JSONDecodeError, AttributeError) as e:
            logging.error(f"Error parsing product script: {str(e)}")
        
        # Clean breadcrumbs
        breadcrumbs_str = ">".join(breadcrumbs) if breadcrumbs else ""
        
        # ITEM YIELD
        item = {}
        item["url"] = url
        item["product_name"] = product_name 
        item["sku"] = sku 
        item["mpn"] = mpn 
        item["breadcrumbs"] = breadcrumbs_str 
        item["rating"] = rating 
        item["reviews"] = reviews 
        item["currency"] = currency 
        item["selling_price"] = selling_price
        item["regular_price"] = regular_price
        item["price_label"] = label
        item["priceValidUntil"] = priceValidUntil
        item["availability"] = availability
        item["seller"] = seller 
        item["image"] = image
        item["features"] = features
        item["description"] = description 
        item["specification"] = specification
        
        logging.info(item)
        
        try:
            ProductDataItem(**item).save()
            logging.info("Saved to database")
        except Exception as e:
            logging.error(f"Error saving to database: {str(e)}")


if __name__ == "__main__":
    parser_obj = Parser()
    parser_obj.start()
    parser_obj.close()