"""from curl_cffi import requests
import json, time
from slugify import slugify
from pymongo import MongoClient
from settings import logging, MONGO_DB, MONGO_COLLECTION_CATEGORY, MONGO_COLLECTION_PRODUCTS

ALGOLIA_URL = "https://8i6wskccnv-dsn.algolia.net/1/indexes/ASDA_PRODUCTS/query"

ALGOLIA_HEADERS = {
    "accept": "*/*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "content-type": "application/x-www-form-urlencoded",
    "origin": "https://www.asda.com",
    "referer": "https://www.asda.com/",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "x-algolia-api-key": "03e4272048dd17f771da37b57ff8a75e",
    "x-algolia-application-id": "8I6WSKCCNV"
}

ALGOLIA_PARAMS = "x-algolia-agent=Algolia%20for%20JavaScript%20(4.25.2)%3B%20Browser"

mongo = MongoClient('mongodb://localhost:27017/')  
db = mongo[MONGO_DB]
current_ts = int(time.time())
# -----------------------------------------------------------
# Load category tree from JSON file
# -----------------------------------------------------------
category_tree = list(db[MONGO_COLLECTION_CATEGORY].find())

# Extract end-level categories only
end_categories = []

for cat in category_tree:
    cat_name = cat.get("name", "")

    for subcat in cat.get("subcategories", []):
        sub_name = subcat.get("name", "")
        sub_id = subcat.get("id")
        sub_url = subcat.get("url")

        sub_subs = subcat.get("sub_subcategories", [])

        if not sub_subs:
            # leaf
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

print(f"FOUND END LEVEL CATEGORIES: {len(end_categories)}")


# -----------------------------------------------------------
# Output file
# -----------------------------------------------------------
outfile = open("asda_products.jsonl", "w", encoding="utf-8")

total_products = 0


# -----------------------------------------------------------
# Crawl each category with pagination
# -----------------------------------------------------------
for idx, category in enumerate(end_categories, 1):

    category_id = category["id"]
    category_name = category["name"]
    category_path = category["full_path"]

    print(f"\n[{idx}/{len(end_categories)}] CATEGORY: {category_path}")
    print("ID:", category_id)

    page = 0

    while True:
        print(f"  Page {page}...", end=" ")

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
                f"( PRIMARY_TAXONOMY.SHELF_ID:'{category_id}' OR "
                f"SECONDARY_TAXONOMY.SHELF_ID:{category_id} ) AND "
                f"PAGE_TAXONOMY:\"{category_path}\""
            )
        }

        url = f"{ALGOLIA_URL}?{ALGOLIA_PARAMS}"

        response = requests.post(
            url,
            headers=ALGOLIA_HEADERS,
            data=json.dumps(payload),
            impersonate="chrome",
            timeout=30
        )

        if response.status_code != 200:
            print("ERROR:", response.status_code)
            break

        data = response.json()

        hits = data.get("hits", [])
        if not hits:
            print(" No hits")
            break

        print(f"{len(hits)} products")

        # -----------------------------------------------------------
        # YOUR REQUIRED EXTRACTION BLOCK (fully integrated)
        # -----------------------------------------------------------
        for product in hits:

            prices_en = product.get("PRICES", {}).get("EN", {})
            shelf_name = product.get("PRIMARY_TAXONOMY", {}).get("SHELF_NAME")

            item = {}
            item["product_id"] = product.get("CIN")
            item["name"] = product.get("NAME")
            item["brand"] = product.get("BRAND")
            item["avg_rating"] = product.get("AVG_RATING")
            item["rating_count"] = product.get("RATING_COUNT")
            item["price"] = prices_en.get("PRICE")
            item["package_size"] = product.get("PACK_SIZE")

            # product URL
            item["url"] = (
                f"https://www.asda.com/groceries/product/"
                f"{slugify(shelf_name)}/{slugify(item['name'])}/{item['product_id']}"
            ) if shelf_name else ""

            item["priceperuom"] = prices_en.get("PRICEPERUOMFORMATTED")
            item["currency"] = "GBP"
            item["stock"] = product.get("STATUS")
            item["promos"] = ",".join(p.get("NAME","") for p in (product.get("PROMOS", {}).get("EN") or []))
            item["wasprice"] = prices_en.get("WASPRICE")
            item["offer"] = prices_en.get("OFFER")

            item["category_id"] = category_id
            item["category_name"] = category_name

            try:
                db[MONGO_COLLECTION_PRODUCTS].insert_one(item)
            except: 
                pass
        # -----------------------------------------------------------
        # PAGINATION CONTROL
        # -----------------------------------------------------------
        nb_pages = data.get("nbPages", 1)

        if page >= nb_pages - 1:
            break

        page += 1
        time.sleep(0.4)



"""
import logging
import json
import time
from curl_cffi import requests
from slugify import slugify
from pymongo import MongoClient
from settings import MONGO_DB, MONGO_COLLECTION_CATEGORY, MONGO_COLLECTION_PRODUCTS

ALGOLIA_URL = "https://8i6wskccnv-dsn.algolia.net/1/indexes/ASDA_PRODUCTS/query"

ALGOLIA_HEADERS = {
    "accept": "*/*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "content-type": "application/x-www-form-urlencoded",
    "origin": "https://www.asda.com",
    "referer": "https://www.asda.com/",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "x-algolia-api-key": "03e4272048dd17f771da37b57ff8a75e",
    "x-algolia-application-id": "8I6WSKCCNV"
}

ALGOLIA_PARAMS = "x-algolia-agent=Algolia%20for%20JavaScript%20(4.25.2)%3B%20Browser"


class Crawler:
    """Crawling Urls"""
    
    def __init__(self):
        self.mongo = MongoClient('mongodb://localhost:27017/')
        
    def start(self):
        """Requesting Start url"""
        
        db = self.mongo[MONGO_DB]
        
        # Load category tree from MongoDB
        category_tree = list(db[MONGO_COLLECTION_CATEGORY].find())
        
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
        
        db = self.mongo[MONGO_DB]
        
        # EXTRACT
        hits = data.get("hits", [])
        
        if hits:
            logging.info(f"  Page {meta.get('page', 0)}... {len(hits)} products")
            
            for product in hits:
                prices_en = product.get("PRICES", {}).get("EN", {})
                shelf_name = product.get("PRIMARY_TAXONOMY", {}).get("SHELF_NAME")
                
                # ITEM YEILD
                item = {}
                item["product_id"] = product.get("CIN")
                item["name"] = product.get("NAME")
                item["brand"] = product.get("BRAND")
                item["avg_rating"] = product.get("AVG_RATING")
                item["rating_count"] = product.get("RATING_COUNT")
                item["price"] = prices_en.get("PRICE")
                item["package_size"] = product.get("PACK_SIZE")
                item["url"] = (
                    f"https://www.asda.com/groceries/product/"
                    f"{slugify(shelf_name)}/{slugify(item['name'])}/{item['product_id']}"
                ) if shelf_name else ""
                item["priceperuom"] = prices_en.get("PRICEPERUOMFORMATTED")
                item["currency"] = "GBP"
                item["stock"] = product.get("STATUS")
                item["promos"] = ",".join(p.get("NAME","") for p in (product.get("PROMOS", {}).get("EN") or []))
                item["wasprice"] = prices_en.get("WASPRICE")
                item["offer"] = prices_en.get("OFFER")
                item["category_id"] = meta['category_id']
                item["category_name"] = meta['category_name']
                
                logging.info(item)
                
                try:
                    db[MONGO_COLLECTION_PRODUCTS].insert_one(item)
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