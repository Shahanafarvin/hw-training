import time
import requests
from mongoengine import connect
from settings import logging, MONGO_DB, HEADERS, QUERY, API_URL 
from items import ProductItem, CategoryItem


class Crawler:
    """Crawler for Matalan products via GraphQL using UIDs stored in MongoDB."""

    def __init__(self):
        connect(db=MONGO_DB, alias="default", host="localhost", port=27017)

    def start(self):
        """Start crawling by reading UIDs from MongoDB."""
        categories = CategoryItem.objects()
        for cat in categories:
            if not cat.uids:
                continue

            for uid in cat.uids:
                logging.info(f"Processing UID: {uid}")
                variables = {
                    "filter": {"category_uid": {"in": [uid]}},
                    "pageSize": 40,
                    "currentPage": 1,
                    "sort": {}
                }
                
                # Fetch first page to get total pages
                resp = requests.post(API_URL, headers=HEADERS, json={"query": QUERY, "variables": variables})
                if resp.status_code != 200:
                    logging.warning(f"Request failed for UID {uid}")
                    continue

                data = resp.json()
               
                total_pages = data.get("data", {}).get("products", {}).get("page_info", {}).get("total_pages", 1)

                # Loop through all pages
                for page in range(1, total_pages + 1):
                    variables["currentPage"] = page
                    resp = requests.post(API_URL, headers=HEADERS, json={"query": QUERY, "variables": variables})
                    self.parse_item(resp, {"category_name" : cat.category_name, "subcategory_name" : cat.sub_category_name, "category_uid": uid, "page": page})
                    time.sleep(1.5)  # polite delay

    def parse_item(self, response, meta):
        """Extract products from GraphQL response and save to MongoDB."""
        data = response.json()
        items = data.get("data", {}).get("products", {}).get("items", [])

        if not items:
            logging.info(f"No items found for {meta}")
            return False

        for item in items:
            product_id = item.get("id")
            name= item.get("name")
            url_key= item.get("url_key")
            brand_name= item.get("brand_name")
            stock_status= item.get("stock_status")
            image_url=item.get("thumbnail",{}).get("url")
            price = item.get("price_range").get("minimum_price").get("final_price").get("value")
            price_before_discount = item.get("price_range").get("minimum_price").get("regular_price").get("value")
            currency=item.get("price_range").get("minimum_price").get("regular_price").get("currency")
            labeling=item.get("product_label")

            # Construct breadcrumbs
            category_name = meta.get("category_name", "").title()
            subcategory_name = meta.get("subcategory_name", "").title()
            breadcrumbs = f"Home / {category_name} / {subcategory_name} / {name}"
            product_data = {

                    "product_id": product_id,
                    "name":name,
                    "url_key": url_key,
                    "brand_name": brand_name,
                    "stock_status": stock_status,
                    "image_url":image_url,
                    "price" : price,
                    "price_before_discount" : price_before_discount,
                    "currency":currency,
                    "labeling":labeling,
                    "category_name":category_name,
                    "breadcrumbs" :breadcrumbs,
                }
          
            try:
                product_item = ProductItem(**product_data)
                product_item.save()
            except Exception as e:
                logging.warning(f"Mongo insert failed: {e}")

        logging.info(f"Saved {len(items)} products for UID {meta['category_uid']} page {meta['page']}")
        return True

    def close(self):
        """Optional cleanup method."""
        logging.info(" product crawling completed.")


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()
