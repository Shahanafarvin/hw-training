import re
import json
from datetime import datetime
from curl_cffi import requests
from parsel import Selector
from pymongo import MongoClient
from settings import MONGO_DB, MONGO_COLLECTION_PRODUCTS, MONGO_COLLECTION_DATA,MONGO_COLLECTION_URL_FAILED,HEADERS, logging


class Parser:
    """parser"""
    
    def __init__(self):
        self.mongo = MongoClient('mongodb://localhost:27017/')
        self.db = self.mongo[MONGO_DB]
    
    def start(self):
        """start code"""
        
        # Fetch all products from MongoDB
        products = list(self.db[MONGO_COLLECTION_PRODUCTS].find())
        
        for product in products:
            url = product.get('url')
            if not url:
                continue
            
            logging.info(f"Processing: {url}")
            
            try:
                response = requests.get(url, headers=HEADERS, impersonate="chrome")
                if response and response.status_code == 200:
                    self.parse_item(url, response, product)
                else:
                    logging.error(f"Failed to fetch {url}: {response.status_code if response else 'No response'}")
                    failed_item = {
                        "url": url,
                        "product_id": product.get("product_id"),
                        "reason": str(e)
                    }
                    self.db[MONGO_COLLECTION_URL_FAILED].insert_one(failed_item)
                    # self.queue.publish(url)##########used for requeuing
            except Exception as e:
                logging.error(f"Error fetching {url}: {e}")
                # self.queue.publish(url)##########used for requeuing
    
    def close(self):
        """connection close"""
        self.mongo.close()
        # self.queue.close()
    
        
    def parse_item(self, url, response, product):
        """item part"""
              
        sel = Selector(text=response.text)
        
        # XPATH
        DESCRIPTION_CONTAINER_XPATH = "//div[@class='css-1qm1lh']"
        IMAGE_SCRIPT_XPATH = "//script[@type='application/ld+json']//text()"
        DESCRIPTION_KEYS_XPATH='.//p[@class="chakra-text css-3gxl7s"]'
        DESCRIPTION_TEXT_XPATHH='normalize-space()'
        DESCRIPTION_VALUE_XPATH='.//p[@class="chakra-text css-1p1nmwo" or @class="chakra-text css-810szs" or @class="chakra-text css-133cdwn"]'
        NUTRITION_XPATH='//div[@class="css-z3gk3"]'
        TYPICALVALUE_XPATH='.//p[@class="chakra-text css-1p1nmwo"]/text()'
        NUTRITION_ROWS_XPATH='.//table//tr'
        NUTRITION_CELLS_XPATH='.//p[@class="chakra-text css-1p1nmwo"]//text() | .//p[@class="chakra-text css-7usuug"]//text()'
        LABELS_XPATH="//p[@class='chakra-text css-h8kb8s']/text()"
        ALLERGY1_XPATH="(//div[@class='chakra-skeleton css-8140fd'])[1]//p//text()"
        ALLERGY2_XPATH="(//div[@class='chakra-skeleton css-8140fd'])[2]//p//text()"
        LIFESTYLE_XPATH="(//div[@class='chakra-skeleton css-8140fd'])[3]//p//text()"
        BREADCRUMBUPC_XPATH="//script[@id='mobify-data']//text()"
        STOCK_XPATH=".//div[@xpath='Out of stock']/text()"

        # EXTRACT
        description_container = sel.xpath(DESCRIPTION_CONTAINER_XPATH)
        image_script = sel.xpath(IMAGE_SCRIPT_XPATH).get()
        nutrition_section = sel.xpath(NUTRITION_XPATH)
        labels=sel.xpath(LABELS_XPATH).getall()
        allergy_1 = sel.xpath(ALLERGY1_XPATH).getall()
        allergy_2 = sel.xpath(ALLERGY2_XPATH).getall()
        lifestyle=sel.xpath(LIFESTYLE_XPATH).getall()
        breadupc_tag=sel.xpath(BREADCRUMBUPC_XPATH).get()
        stock=sel.xpath(STOCK_XPATH).get()

        #CLEAN
        def remove_css(text):
                if not text:
                    return ""
                else:
                    # Remove all `.something{...}` patterns (CSS rules)
                    text = re.sub(r'\.[\w\-]+\s*[^}]*\{[^}]*\}\s*', '', text)

                    # Optionally remove multiple CSS blocks in a row
                    text = re.sub(r'(\.[\w\-]+\s*[^}]*\{[^}]*\}\s*)+', '', text)

                    return text.strip()
                
        # Parse description sections
        description_data = {}
        for des in description_container:
            keys = des.xpath(DESCRIPTION_KEYS_XPATH)
            
            for key_node in keys:
                key = key_node.xpath(DESCRIPTION_TEXT_XPATHH).get()
                
                if key:
                    # Find value nodes (section content)
                    value_nodes = des.xpath(DESCRIPTION_VALUE_XPATH) 
                    # Join all text inside the container
                    values = [
                        v.xpath(DESCRIPTION_TEXT_XPATHH).get()
                        for v in value_nodes
                        if v.xpath(DESCRIPTION_TEXT_XPATHH).get()
                    ]
                    
                    if values:
                        description_data[key] = " ".join(values)
        
        # Parse images from JSON-LD script
        if image_script:
            json_data = json.loads(image_script)
            image=json_data.get("image")
    

       # Select the main nutrition section container
        if nutrition_section:
            # Extract heading: "Typical values per 100g"
            typical_values_text = nutrition_section.xpath(TYPICALVALUE_XPATH).get()
            typical_values_text = typical_values_text.strip() if typical_values_text else ""

            # Extract table rows from only inside css-z3gk3
            rows = nutrition_section.xpath(NUTRITION_ROWS_XPATH)

            nutritional_values = []

            for row in rows:
                cells = row.xpath(NUTRITION_CELLS_XPATH).getall()
                cells = [c.strip() for c in cells if c.strip()]
                if cells:
                    nutritional_values.append(" - ".join(cells))

            # Build final paragraph
            nutritional_paragraph = remove_css(f"{typical_values_text or ''}. {' ,'.join(nutritional_values)}")

        else:
            nutritional_paragraph=""
        #labels
        labels=",".join(labels)
        if "Frozen" in labels:
            frozen= "Frozen"
        else: 
            frozen=""
        #allergy
        allergy = ""
        # only join if data exists
        parts = []
        if allergy_1:
            parts.append(" ".join(allergy_1).strip())
        if allergy_2:
            parts.append(" ".join(allergy_2).strip())
        allergy = ", ".join(parts)  
        #lifestyle
        lifestyle=",".join(lifestyle)
        #breadcrumbs and upc extraction
        json_text=json.loads(breadupc_tag)
        breadcrumb=json_text.get("__PRELOADED_STATE__",{}).get("pageProps",{}).get("pageData",{}).get("initialProduct",{}).get("c_categoryTree",{}).get("parentCategoryTree",[])
        breadcrumb_items=[item.get("name") for item in breadcrumb]
        breadcrumb_path = " > ".join(breadcrumb_items)
        breadcrumbs=f"Home > {breadcrumb_path} > {product.get('name')}"

        upc=json_text.get("__PRELOADED_STATE__",{}).get("pageProps",{}).get("pageData",{}).get("initialProduct",{}).get("upc")
        #stock
        stock= False if stock == "Out of stock" else True
        competitor_name="asda"
        extraction_date=datetime.now().strftime("%Y-%m-%d")
        #grammage quantity and unit 
        size = product.get("package_size")
        if size:
            size = str(size).strip()
            match = re.match(r"^([0-9.,\-*]+)\s*(.*)$", size)

            if match:
                qty_raw = match.group(1).replace(",", ".")    # normalize comma
                unit_raw = match.group(2).strip().lower()     # lowercase unit

                # convert to float if simple number
                try:
                    if "*" in qty_raw or "-" in qty_raw:
                        qty = qty_raw   # keep complex numeric expressions
                    else:
                        qty = float(qty_raw)
                except:
                    qty = qty_raw
            else:
                qty, unit_raw = "", size.lower()
        else:
            qty, unit_raw = "", ""
        #hierarchy levels
        # Split breadcrumb by '>' and clean each part
        hierarchy_parts = [b.strip() for b in breadcrumbs.split(">") if b.strip()]

        # Create up to 7 hierarchy levels (fill missing ones with "")
        hierarchy_levels = {}
        for i in range(7):
            hierarchy_levels[f"producthierarchy_level{i+1}"] = hierarchy_parts[i] if i < len(hierarchy_parts) else ""
        #price details
        price=product.get("price")
        was_price=product.get("wasprice")
        if not was_price:
            regular_price=f"{float(price):.2f}"
            selling_price=f"{float(price):.2f}"
            promotion_price=""
            price_was=""
        else:
            regular_price=f"{float(was_price):.2f}"
            price_was=f"{float(was_price):.2f}"
            selling_price=f"{float(price):.2f}"
            promotion_price=f"{float(price):.2f}"
        #description
        product_description=remove_css(", ".join(f"{k}: {v}" for k, v in description_data.items()))
        storage_instructions=remove_css(description_data.get("Storage"))
        net_content=remove_css(description_data.get("Net Content"))
        preparation_instructions=remove_css(description_data.get("Cooking Guidelines"))
        instructionforuse=remove_css(description_data.get("Preparation and Usage"))
        country_of_origin=remove_css(description_data.get("Country of Origin"))
        features=remove_css(description_data.get("Features"))
        manufacturer_address=remove_css(description_data.get("Manufacturer Address"))
        recycling_information=remove_css(description_data.get("Recycling Info"))
        ingredients=remove_css(description_data.get("Ingredients"))
        Warning=remove_css(description_data.get("Safety Warning"))
        warnings=Warning.replace("WARNING","").strip()
        #promotion details
        offer=product.get("offer")
        promo=product.get("promos")
        if offer == "List": 
            promotion_description=promo
        else:
            promotion_description=promo or offer
   
        product_unique_key=f"{product.get('product_id')}P"
        

        # ITEM YEILD
        item = {}
        item["unique_id"] = product.get("product_id")
        item["competitor_name"] = competitor_name
        item["extraction_date"] = extraction_date
        item["product_name"] = product.get("name")
        item["brand"] = product.get("brand")
        item["grammage_quantity"] = qty
        item["grammage_unit"] = unit_raw
        item["producthierarchy_level1"] = hierarchy_levels.get("producthierarchy_level1")
        item["producthierarchy_level2"] = hierarchy_levels.get("producthierarchy_level2")
        item["producthierarchy_level3"] = hierarchy_levels.get("producthierarchy_level3")
        item["producthierarchy_level4"] = hierarchy_levels.get("producthierarchy_level4")
        item["producthierarchy_level5"] = hierarchy_levels.get("producthierarchy_level5")
        item["producthierarchy_level6"] = hierarchy_levels.get("producthierarchy_level6")
        item["producthierarchy_level7"] = hierarchy_levels.get("producthierarchy_level7")
        item["regular_price"] = regular_price
        item["selling_price"] = selling_price   
        item["promotion_price"] = promotion_price
        item["price_was"] = price_was  
        item["promotion_description"] = promotion_description  
        item["price_per_unit"] = product.get("priceperuom")
        item["currency"] = product.get("currency")
        item["breadcrumb"] = breadcrumbs
        item["pdp_url"] = url
        item["product_description"] = product_description
        item["storage_instructions"] =storage_instructions
        item["preparation_instructions"] = preparation_instructions
        item["instructionforuse"] = instructionforuse
        item["country_of_origin"] = country_of_origin
        item["allergens"] = allergy
        item["nutritional_information"] =nutritional_paragraph
        item["labelling"]= labels
        item["frozen"] = frozen
        item["rating"] = product.get("avg_rating")
        item["review"] = product.get("rating_count")
        item["image_url_1"] = image
        item["competitor_product_key"] = product.get("product_id")
        item["upc"] = upc
        item['Features'] = features
        item["dietary_lifestyle"] = lifestyle
        item["manufacturer_address"] = manufacturer_address
        item["recycling_information"] = recycling_information
        item["site_shown_uom"] = size
        item["ingredients"] = ingredients
        item["instock"] = stock
        item["product_unique_key"] = product_unique_key
        item["warning"]= warnings
        item["netcontent"]=net_content
        
    
        #logging.info(item)
      
        try:
            self.db[MONGO_COLLECTION_DATA].insert_one(item)
        except Exception as e:
            logging.error(f"Failed to insert item: {e}")


if __name__ == "__main__":
    parser_obj = Parser()
    parser_obj.start()
    parser_obj.close()