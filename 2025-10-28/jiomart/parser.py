import re
import json
import time
import random
import requests
from parsel import Selector
from mongoengine import connect, disconnect
from items import ProductItem, ProductEnrichedItem
from settings import MONGO_DB, MONGO_URI, logger, price_headers, cookies, review_headers

class Parser:
    """Enrich Jiomart products with PDP, pricing, and review info"""

    def __init__(self):
        connect(db=MONGO_DB, host=MONGO_URI, alias="default")
    
    def clean_text_list(self,text_list):
        """Clean and join text content from XPath lists."""
        return " ".join([t.strip() for t in text_list if t.strip()])
    
    def close(self):
        disconnect(alias="default")
        logger.info(" MongoDB connection closed after enrichment.")
        
    def parse_item(self,pdp_url):
        """Extract product description and info section from PDP."""
        try:
            resp = requests.get(pdp_url, timeout=25)
            resp.raise_for_status()
            sel = Selector(text=resp.text)
            info={}
            title = sel.xpath("//div[@id='pdp_product_name']/text()").get()
            images=sel.xpath('//div[contains(@class,"swiper-thumb-slides swiper-slide")]//img/@data-src').getall()
            #print(images)
            description = self.clean_text_list(sel.xpath('//div[@id="pdp_description"]//text()').getall())
            info_tables = sel.xpath('//div[@id="pdp_product_information"]/table')
            for table in info_tables:
                rows = table.xpath(".//tr")
                for row in rows:
                    key = row.xpath(".//th//text()").get()
                    value = row.xpath(".//td//text()").get()
                    if key and value:
                        key_clean = re.sub(r"[:：]", "", key.strip())
                        info[key_clean] = value.strip()
            product_id=sel.xpath('//div[@id="crfe_widget"]/@data-product-id').get()
            return {
                "title": title,
                "description": description,
                "product_info": info,
                "images": images,
                "product_id": product_id,   
            }

        except Exception as e:
            logger.error(f" PDP fetch failed for {pdp_url}: {e}")
            return {}
        
    def parse_price(self,product_id,pdp_url):
        """Fetch pricing and stock data from productdetails API."""
        url = f"https://www.jiomart.com/catalog/productdetails/get/{product_id}"
        price_headers["referer"] = pdp_url
        try:
            resp = requests.get(url, headers=price_headers, cookies=cookies, timeout=25)
            resp.raise_for_status()
            data = resp.json().get("data", {})
            return {
                "availability_status": data.get("availability_status", ""),
                "discount_pct": data.get("discount_pct", ""),
                "mrp": data.get("mrp", ""),
                "selling_price": data.get("selling_price", ""),
                "teaser_tag": data.get("teaser_tag", ""),
                "payment_tags": data.get("payment_tags", ""),
            }
        except Exception as e:
            logger.error(f" Price fetch failed for {product_id}: {e}")
            return {}
        
    def parse_review(self,alternate_id):
        """Fetch average rating and review count using alternate ID."""
        if not alternate_id:
            return {}

        alternate_id = alternate_id.strip().replace('"', '')
        
        url = f"https://reviews-ratings.jio.com/customer/op/v1/review/product-statistics/{alternate_id}"

        try:
            resp = requests.get(url, headers=review_headers, timeout=20)
            print(resp.url)
            resp.raise_for_status()
            data = resp.json().get("data", {})
            return {
                "averageRating": data.get("averageRating"),
                "ratingsCount": data.get("ratingsCount"),
            }
        except Exception as e:
            logger.error(f"Review fetch failed for {alternate_id}: {e}")
            return {}
    
    def parse_data(self):
        """Iterate through all products and enrich"""
        products = ProductItem.objects.only("unique_id", "pdp_url", "alternate_ids","brand","title","images","category_path")
        logger.info(f"Found {len(products)} products to enrich.")

        for i, prod in enumerate(products, start=1):
            try:
                pid = str(prod.unique_id)
                pdp_url = prod.pdp_url
                alt_id = prod.alternate_ids or ""
                brand= prod.brand or ""
                title= prod.title or ""
                images= prod.images or []
                category_path= prod.category_path or []

                logger.info(f"🔹 Enriching [{i}] Product ID: {pid}")

                # Step 1: Fetch PDP details
                pdp_data = self.parse_item(pdp_url)
                if not pdp_data:
                    continue
                alternate_id = pdp_data.get("product_id", alt_id)
                # Step 2: Fetch Price data
                price_data = self.parse_price(pid,pdp_url)

                # Step 3: Fetch Review data
                review_data = self.parse_review(alternate_id)
                
                # Merge everything
                enriched_doc = ProductEnrichedItem(
                    product_id=pid,
                    pdp_url=pdp_url,
                    brand=brand,
                    title=title,
                    images=pdp_data.get("images", images),
                    category_path=category_path,
                    description=pdp_data.get("description", ""),
                    product_info=pdp_data.get("product_info", {}),
                    availability=price_data.get("availability_status", ""),
                    discount=price_data.get("discount_pct", ""),
                    mrp=price_data.get("mrp", ""),
                    selling_price=price_data.get("selling_price", ""),
                    average_rating=review_data.get("averageRating"),
                    review_count=review_data.get("ratingsCount"),
                    alternate_ids=alt_id,
                )

                enriched_doc.save()
                logger.info(f" Saved enriched product {pid}")

                time.sleep(random.uniform(1.5, 3.5))  # avoid rate limits

            except Exception as e:
                logger.error(f"Error enriching product {prod.unique_id}: {e}")
                continue

    


# -----------------------------
# Run Script
# -----------------------------
if __name__ == "__main__":
    parser_obj = Parser()
    parser_obj.parse_data()
    parser_obj.close()
