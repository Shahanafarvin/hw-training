#!/usr/bin/env python3
import logging
import time
import re
import os
from datetime import datetime
from urllib.parse import urljoin

import requests
from lxml import html
from pymongo import MongoClient, ASCENDING

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


class FressnapfProductDetailScraper:
    BASE_URL = "https://www.fressnapf.de/"

    def __init__(
        self,
        proxy_string: str,
        mongo_uri: str = "mongodb://localhost:27017/",
        db_name: str = "fressnapf",
        request_delay: float = 0.6,
    ):
        self.session = requests.Session()
        self.session.proxies.update({"https": proxy_string})
        self.session.verify = False  # disable TLS verify if proxy requires
        self.delay = request_delay

        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]

        # read from products collection, write to product_details collection
        self.urls_col = self.db["products"]
        self.details_col = self.db["product_details"]

        # index to avoid duplicate inserts
        self.details_col.create_index([("pdp_url", ASCENDING)], unique=True)

    def fetch_tree(self, url):
        """Fetch URL and return parsed lxml tree."""
        try:
            logging.info("GET %s", url)
            resp = self.session.get(url, timeout=60)
            resp.raise_for_status()
            return html.fromstring(resp.text)
        except Exception as e:
            logging.warning("Failed to fetch %s : %s", url, e)
            return None
        finally:
            time.sleep(self.delay)

    def parse_product_page(self, url):
        """Extract detailed product info."""
        tree = self.fetch_tree(url)
        if tree is None:
            return None

        try:
            # Extract unique product ID
            unique_id=tree.xpath("//section[@class='accordion-item-content']//p/text()")
            unique_id = unique_id[0].replace("Art.Nr.: ","").strip() if unique_id else None
            # Extract product title and brand
            title = " ".join(tree.xpath("//h1[@class='heading--icon h4 heading pos-title']//text()"))
            brand = tree.xpath("//a[@data-id='pdp-brand-link']//text()")
        
            # Extract grammage and unit from title
            # Pattern: capture number + unit in separate groups
            pattern = r'(?P<amount>\d+(?:[\.,]\d+)?)' \
                    r'(?:\s?[xX]\s?(?P<multiplier>\d+))?' \
                    r'\s?(?P<unit>kg|g|ml|l)'
            match = re.search(pattern, title, flags=re.IGNORECASE)

            if match:
                amount = match.group("amount")         # "4" or "9" or "1.5"
                multiplier = match.group("multiplier") # "250" or None
                unit = match.group("unit")             # "g" or "kg"

                if multiplier:
                    grammage_quantity = f"{amount}*{multiplier}"   # "4*250"
                else:
                    grammage_quantity = amount                    # "9" or "1.5"

                grammage_unit = unit


            # Extract breadcrumb items
            breadcrumbs = [ ">".join(li.xpath(".//text()")).strip() for li in tree.xpath("//ul[@class='b-items']/li") ]

            # Assign hierarchy levels
            hierarchy = {f"producthierarchy_level{i+1}": b for i, b in enumerate(breadcrumbs)}
            #extracting price per unit
            price_per_unit = tree.xpath("//div[contains(@class,'p-per-unit')]//text()")

            #extracting price
            price = tree.xpath("//span[contains(@class,'p-regular-price-value')]//text()")
            #extrcting product description
            description=tree.xpath("//ul[@class='list list--small-bullets']")
            description=",".join(description[0].xpath(".//text()")).strip() if description else None
            #extracting reviews and ratings
            rating = tree.xpath("//div[@class='bv_avgRating_component_container notranslate']//text()")
            print(rating)
            rating = rating[0].strip() if rating else None
            reviews = tree.xpath("//div[@class='bv_numReviews_text']//text()")
            print(reviews)
            reviews = reviews[0].replace("(","").replace(")","").strip() if reviews else None
            #extracting images
            def save_images(tree, uniqueid, save_folder="product_images", max_images=6):
                # extract image URLs from slider
                img_urls = tree.xpath('//div[@class="g-slider"]//a/@href')
                os.makedirs(save_folder, exist_ok=True)

                # initialize dictionary with None
                images_dict = {f'file_name_{i}': None for i in range(1, max_images+1)}
                images_dict.update({f'image_url_{i}': None for i in range(1, max_images+1)})

                for idx, url in enumerate(img_urls[:max_images], start=1):
                    url= url

                    images_dict[f'file_name_{idx}'] = f"{uniqueid}_{idx}.PNG"
                    images_dict[f'image_url_{idx}'] = url

                    # download the image
                    try:
                        resp = self.session.get(url, stream=True, timeout=60)
                        if resp.status_code == 200:
                            file_path = os.path.join(save_folder, images_dict[f'file_name_{idx}'])
                            with open(file_path, "wb") as f:
                                for chunk in resp.iter_content(1024):
                                    f.write(chunk)
                            print(f"Saved {file_path}")
                        else:
                            print(f"Failed to download {url}")
                    except Exception as e:
                        print(f"Error downloading {url}: {e}")

                    return images_dict
                
            image_dict = save_images(tree, unique_id, save_folder="product_images")
            #extracting ingredients
            ingredients_xpath = ('//div[contains(@class,"accordion-item")]'
                '[.//h2[normalize-space()="Inhaltsstoffe"]]'
                '//section//text()')
            ingredients = " ".join(tree.xpath(ingredients_xpath)).strip()

            #extracting feeding instruction
            feeding_instruction=",".join(tree.xpath('//div[@class="feeding-suggestion"]/p//text()'))

            return {
                "unique_id": unique_id,
                "competitor_name": "fressnapf",
                "store_name": None,
                "store_addressline1": None,
                "store_addressline2": None,
                "store_suburb": None,
                "store_state": None,
                "store_postcode": None,
                "store_addressid": None,
                "extraction_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "product_name": title or  None,
                "brand":brand[0].strip() if brand else None,
                "brand_type": None,   # not available
                "grammage_quantity": grammage_quantity or None, 
                "grammage_unit": grammage_unit or None,
                "drained_weight": None,  # not available
                "producthierarchy_level1": "home",  
                "producthierarchy_level2": hierarchy.get("producthierarchy_level2"),  
                "producthierarchy_level3": hierarchy.get("producthierarchy_level3"),  
                "producthierarchy_level4": hierarchy.get("producthierarchy_level4"),  
                "producthierarchy_level5": hierarchy.get("producthierarchy_level5"),  
                "producthierarchy_level6": hierarchy.get("producthierarchy_level6"), 
                "producthierarchy_level7": hierarchy.get("producthierarchy_level7"),
                "regular_price": price[0].replace("€","").strip() if price else None,
                "selling_price": price[0].replace("€","").strip() if price else None,  
                "price_was": None,  # not available
                "promotion_price": None,  # not available
                "promotion_valid_from": None,  # not available
                "promotion_valid_upto": None,  # not available
                "promotion_type": None,  # not available
                "percentage_discount": None,  # not available
                "promotion_description": None,  # not available
                "package_sizeof_selling" : None,  # not available
                "per_unit_sizedescription" : None,  # not available
                "price_valid_from": None,  # not available
                "price_per_unit": price_per_unit[0].replace("(","").replace(")","").strip() if price_per_unit else None,
                "multi_buy_item_count": None,  # not available
                "multi_buy_items_price_total": None,  # not available
                "currency": "€",
                "breadcrumb":breadcrumbs or None,
                "pdp_url": url,
                "variants": None,  # not available
                "product_description": description or None,
                "instructions": None,  # not available
                "storage_instructions": None,  # not available
                "preparationinstructions": None,  # not available
                "instructionforuse": None,  # not available
                "country_of_origin": None,  # not available
                "allergens": None,  # not available
                "age_of_the_product": None,  # not available
                "age_recommendations": None,  # not available
                "flavour": None,  # not available
                "nutritions": None,  # not available
                "nutritional_information": None,  # not available
                "vitamins": None,  # not available
                "labelling": None,  # not available
                "grade": None,  # not available
                "region": None,  # not available
                "packaging": None,  # not available
                'receipies': None, # not available
                'processed_food': None, # not available
                'barcode': None, # not available
                'frozen': None, # not available
                'chilled': None, # not available
                'organictype': None, # not available
                'cooking_part': None, # not available
                'Handmade': None, # not available
                'max_heating_temperature': None, # not available
                'special_information': None, # not available
                'label_information': None, # not available
                'dimensions': None, # not available
                'special_nutrition_purpose': None, # not available
                'feeding_recommendation': feeding_instruction or None,
                'warranty': None, # not available
                'color': None, # not available
                'model_number': None, # not available
                'material': None, # not available
                'usp': None, # not available
                'dosage_recommendation': None, # not available
                'tasting_note': None, # not available
                'food_preservation': None, # not available
                'size': None, # not available
                'rating': rating or None, 
                'review': reviews or  None, 
                'file_name_1': image_dict.get('file_name_1'),     
                'image_url_1': image_dict.get('image_url_1'),
                'file_name_2': image_dict.get('file_name_2'),
                'image_url_2': image_dict.get('image_url_2'),
                'file_name_3': image_dict.get('file_name_3'),
                'image_url_3': image_dict.get('image_url_3'),
                'file_name_4': image_dict.get('file_name_4'),
                'image_url_4': image_dict.get('image_url_4'),
                'file_name_5': image_dict.get('file_name_5'),
                'image_url_5': image_dict.get('image_url_5'),
                'file_name_6': image_dict.get('file_name_6'),
                'image_url_6': image_dict.get('image_url_6'),   
                'competitor_product_key': None, 
                'fit_guide': None, 
                'occasion': None, 
                'material_composition': None, 
                'style': None, 
                'care_instructions': None, 
                'heel_type': None, 
                'heel_height': None, 
                'upc': None, 
                'features': None, 
                'dietary_lifestyle': None, 
                'manufacturer_address': None, 
                'importer_address': None, 
                'distributor_address': None, 
                'vinification_details': None, 
                'recycling_information': None, 
                'return_address': None, 
                'alchol_by_volume': None, 
                'beer_deg': None, 
                'netcontent': None, 
                'netweight': None, 
                'site_shown_uom': None, 
                'ingredients': ingredients or None, 
                'random_weight_flag': None, 
                'instock': None, 
                'promo_limit': None, 
                'product_unique_key': unique_id + "P" if unique_id else None, 
                'multibuy_items_pricesingle': None, 
                'perfect_match': None, 
                'servings_per_pack': None, 
                'Warning': None, 
                'suitable_for': None, 
                'standard_drinks': None, 
                'environmental': None, 
                'grape_variety': None, 
                'retail_limit': None
                
            }
        except Exception as e:
            logging.error("Parse error at %s : %s", url, e)
            return None

    def run(self, limit=None):
        """Go through product URLs, scrape detail page, and save to product_details."""
        cursor = self.urls_col.find({}, {"product_url": 1, "_id": 0})
        if limit:
            cursor = cursor.limit(limit)

        for doc in cursor:
            url = doc["product_url"]

            # skip if already scraped
            if self.details_col.find_one({"product_url": url}):
                logging.info("Already scraped %s, skipping", url)
                continue

            product_data = self.parse_product_page(url)
            if product_data:
                try:
                    self.details_col.insert_one(product_data)
                    logging.info("Saved details for %s", url)
                except Exception as e:
                    logging.warning("Insert failed for %s : %s", url, e)


if __name__ == "__main__":
    PROXY = "scraperapi.follow_redirect=false.retry_404=true.country_code=de.session_number=143:e43c5dbeb53e7947234925142941f6da@proxy-server.scraperapi.com:8001"

    scraper = FressnapfProductDetailScraper(proxy_string=PROXY, mongo_uri="mongodb://localhost:27017/", db_name="fressnapf")
    scraper.run(limit=50)  # test run on first 50 product URLs
