import requests
import unicodedata
import re
import time
import random
from mongoengine import connect
from items import ProductCategoryItem, ProductItem
from settings import MONGO_URI, MONGO_DB, CRAWLER_HEADERS, logging

class AuchanCrawler:
    """Crawler for Auchan products using leaf category IDs"""

    def __init__(self):
        connect(db=MONGO_DB, host=MONGO_URI)

    def start(self):
        """Fetch all leaf category IDs and crawl them"""
        leaf_ids = self.get_leaf_category_ids()
        logging.info(f"Total leaf categories to crawl: {len(leaf_ids)}")

        for cat_id in leaf_ids:
            page = 1
            while True:
                api_url = f"https://auchan.hu/api/v2/cache/products?page={page}&itemsPerPage=8&categoryId={cat_id}&cacheSegmentationCode=&hl=hu"
                try:
                    response = requests.get(api_url, headers=CRAWLER_HEADERS)
                    logging.info(f"Requesting {api_url} → Status Code: {response.status_code}")
                    if response.status_code != 200:
                        break

                    data = response.json()
                    self.parse_item(data)

                    # Stop if no more pages
                    page_count = data.get("pageCount", 1)
                    if page >= page_count:
                        break

                    page += 1
                    time.sleep(random.uniform(1.5, 3.5))

                except Exception as e:
                    logging.error(f"Error while crawling category {cat_id}, page {page}: {e}")
                    break

    def get_leaf_category_ids(self):
        """Traverse ProductCategoryItem tree and return all leaf category IDs"""
        leaf_ids = []

        def traverse(node):
            if not node.subcategories:
                leaf_ids.append(node.category_id)
            else:
                for sub in node.subcategories:
                    traverse(sub)

        for top_cat in ProductCategoryItem.objects():
            traverse(top_cat)

        return leaf_ids

    def parse_item(self, data):
        """Parse JSON items and save/update in MongoEngine"""
        for item in data.get("results", []):
            variant = item.get("selectedVariant", {})
            name = variant.get("name", "")
            sku = variant.get("sku", "")

            slug = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
            slug = re.sub(r'[^a-zA-Z0-9]+', '-', slug.strip().lower())
            product_url = f"https://auchan.hu/shop/{slug}.p-{sku}"

            product_data = {
                "title": name,
                "brand": item.get("brandName"),
                "breadcrumbs": " > ".join([cat.get("name", "") for cat in item.get("categories", []) if "name" in cat]),
                "images": variant.get("media", {}).get("images", []),
                "grammage_quantity": variant.get("packageInfo", {}).get("packageSize"),
                "grammage_unit": variant.get("packageInfo", {}).get("packageUnit"),
                "unit_price": variant.get("packageInfo", {}).get("unitPrice", {}).get("net"),
                "regular_price": variant.get("price", {}).get("net"),
                "currency": variant.get("price", {}).get("currency"),
                "sku": sku,
                "product_id": variant.get("productId"),
                "selectvalue": variant.get("selectValue"),
                "details": variant.get("details", []),
                "rating" : item.get("reviewSum",{}).get("average"),
                "review": item.get("reviewSum",{}).get("sumCount"),
                "product_url": product_url,
            }

            try:
                ProductItem.objects(product_url=product_url).update_one(
                    set__title=product_data["title"],
                    set__brand=product_data["brand"],
                    set__breadcrumbs=product_data["breadcrumbs"],
                    set__images=product_data["images"],
                    set__grammage_quantity=product_data["grammage_quantity"],
                    set__grammage_unit=product_data["grammage_unit"],
                    set__unit_price=product_data["unit_price"],
                    set__regular_price=product_data["regular_price"],
                    set__currency=product_data["currency"],
                    set__sku=product_data["sku"],
                    set__product_id=product_data["product_id"],
                    set__selectvalue=product_data["selectvalue"],
                    set__details=product_data["details"],
                    set__rating=product_data["rating"],
                    set__review=product_data["review"],
                    upsert=True,
                )
                logging.info(f"Saved/Updated product: {name} → {product_url}")
            except Exception as e:
                logging.error(f"Failed to save product {name}: {e}")

    def close(self):
        logging.info("Crawler finished.")


if __name__ == "__main__":
    crawler = AuchanCrawler()
    crawler.start()
    crawler.close()
