
import json
import time
from curl_cffi import requests
from slugify import slugify
from pymongo import MongoClient
from settings import MONGO_DB, MONGO_COLLECTION_CATEGORY,MONGO_COLLECTION_PRODUCTS,logging,ALGOLIA_URL,ALGOLIA_PARAMS,ALGOLIA_HEADERS

class Crawler:
    """Crawling Urls"""
    
    def __init__(self):
        self.mongo = MongoClient('mongodb://localhost:27017/')
        self.db = self.mongo[MONGO_DB]
        self.db[MONGO_COLLECTION_PRODUCTS].create_index("url", unique=True)

        
    def start(self):
        """Requesting Start url"""
        
        # Load category tree from MongoDB
        category_tree = list(self.db[MONGO_COLLECTION_CATEGORY].find())
        
        # Extract end-level categories
        end_categories = []
        for cat in category_tree:
            cat_name = cat.get("name", "")
            for subcat in cat.get("subcategories", []):
                sub_name = subcat.get("name", "")
                sub_id = subcat.get("id")
                sub_subs = subcat.get("sub_subcategories", [])
                
                if not sub_subs:
                    end_categories.append({
                        "id": sub_id,
                        "name": sub_name,
                        "full_path": f"{cat_name} > {sub_name}"
                    })
                else:
                    for s in sub_subs:
                        s_name = s.get("name", "")
                        s_id = s.get("id")
                        s2_children = s.get("sub_subcategories", [])
                        
                        if not s2_children:
                            end_categories.append({
                                "id": s_id,
                                "name": s_name,
                                "full_path": f"{cat_name} > {sub_name} > {s_name}"
                            })
                        else:
                            for x in s2_children:
                                end_categories.append({
                                    "id": x.get("id"),
                                    "name": x.get("name", ""),
                                    "full_path": f"{cat_name} > {sub_name} > {s_name} > {x.get('name','')}"
                                })
        
        logging.info(f"FOUND END LEVEL CATEGORIES: {len(end_categories)}")
        
        for idx, category in enumerate(end_categories, 1):
            meta = {}
            meta['category_id'] = category["id"]
            meta['category_name'] = category["name"]
            meta['category_path'] = category["full_path"]
            
            logging.info(f"\n[{idx}/{len(end_categories)}] CATEGORY: {meta['category_path']}")
            logging.info(f"ID: {meta['category_id']}")
            
            page = meta.get("page", 0)  # initialising page for pagination
            api_url = f"{ALGOLIA_URL}?{ALGOLIA_PARAMS}"  # generate api Url
            
            while True:
                current_ts = int(time.time())
                
                payload = {
                    "query": "",
                    "clickAnalytics": True,
                    "analytics": True,
                    "hitsPerPage": 60,
                    "page": page,
                    "removeWordsIfNoResults": "allOptional",
                    "optionalFilters": ["STOCK.4565:1<score=50000>"],
                    "attributesToRetrieve": [
                        "STATUS", "BRAND", "CIN", "NAME", "AVG_RATING", "RATING_COUNT",
                        "ICONS", "PRICES.EN", "SALES_TYPE", "MAX_QTY", "STOCK.4565",
                        "IS_FROZEN", "IS_BWS", "PROMOS.EN", "LABEL", "LABEL_START_DATE",
                        "LABEL_END_DATE", "IS_SPONSORED", "PRODUCT_TYPE", "CIN_ID",
                        "PRIMARY_TAXONOMY", "IMAGE_ID", "PACK_SIZE", "PHARMACY_RESTRICTED",
                        "CS_YES", "CS_TEXT", "IS_FTO", "PURCHASE_START_DATE_FTO",
                        "PURCHASE_END_DATE_FTO", "DELIVERY_SLOT_START_DATE_FTO",
                        "END_DATE", "START_DATE", "SIZE_DESC", "REWARDS", "SHOW_PRICE_CS", "ID"
                    ],
                    "facets": ["BRAND", "NUTRITIONAL_INFO.*"],
                    "filters": (
                        f"(STATUS:A OR STATUS:I) AND END_DATE>{current_ts} AND "
                        f"( PRIMARY_TAXONOMY.SHELF_ID:'{meta['category_id']}' OR "
                        f"SECONDARY_TAXONOMY.SHELF_ID:{meta['category_id']} ) AND "
                        f"PAGE_TAXONOMY:\"{meta['category_path']}\""
                    )
                }
                
                response = requests.post(
                    api_url,
                    headers=ALGOLIA_HEADERS,
                    data=json.dumps(payload),
                    impersonate="chrome",
                    timeout=30
                )
                
                if response.status_code == 200:
                    is_next = self.parse_item(response, meta)
                    if not is_next:
                        logging.info("Pagination completed")
                        break
                    # pagination crawling
                    page += 1
                    meta["page"] = page
                    time.sleep(0.4)
                else:
                    logging.error(f"ERROR: {response.status_code}")
                    break
                    # self.queue.publish(data) ##########used for requeuing
    
    def parse_item(self, response, meta):
        """item part"""
        try:
            data = response.json()
        except:
            return False
        
        # EXTRACT
        products = data.get("hits", [])
        
        if products:
            logging.info(f"page {meta.get('page')} - {len(products)} found")

            for product in products:
                prices_en = product.get("PRICES", {}).get("EN", {})
                shelf_name = product.get("PRIMARY_TAXONOMY", {}).get("SHELF_NAME")
                product_id = product.get("CIN")
                name = product.get("NAME")
                brand = product.get("BRAND")
                avg_rating = product.get("AVG_RATING")
                rating_count = product.get("RATING_COUNT")
                price = prices_en.get("PRICE")
                package_size = product.get("PACK_SIZE")
                url = (
                    f"https://www.asda.com/groceries/product/"
                    f"{slugify(shelf_name)}/{slugify(name)}/{product_id}"
                ) if shelf_name else ""
                priceperuom = prices_en.get("PRICEPERUOMFORMATTED")
                currency = "GBP"
                promos = ",".join(p.get("NAME","") for p in (product.get("PROMOS", {}).get("EN") or []))
                was_price = prices_en.get("WASPRICE")
                offer = prices_en.get("OFFER")
                category_id = meta['category_id']
                category_name = meta['category_name']
                
                # ITEM YEILD
                item = {}
                item["product_id"] = product_id
                item["name"] = name
                item["brand"] = brand
                item["avg_rating"] = avg_rating
                item["rating_count"] = rating_count
                item["price"] = price
                item["package_size"] = package_size
                item["url"] = url
                item["priceperuom"] = priceperuom
                item["currency"] = currency
                item["promos"] = promos
                item["wasprice"] = was_price
                item["offer"] = offer
                item["category_id"] = category_id
                item["category_name"] = category_name
                
                #logging.info(item)
                
                try:
                    self.db[MONGO_COLLECTION_PRODUCTS].insert_one(item)
                except:
                    pass
            
            return True
        
        return False
    
    def close(self):
        """Close function for all module object closing"""
        self.mongo.close()
        # self.queue.close()


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()