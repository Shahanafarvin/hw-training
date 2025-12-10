from curl_cffi import requests
from pymongo import MongoClient
from settings import logging,HEADERS,MONGO_DB,MONGO_COLLECTION_CATEGORY

BASE_URL = "https://ghs-mm.asda.com/static"


class CategoryCrawler:
    """Crawling Asda Categories"""
    
    def __init__(self):
        # MongoDB connection
        self.mongo = MongoClient('mongodb://localhost:27017/')  
        self.db = self.mongo[MONGO_DB]  
        
    def start(self):
        """Start crawling categories"""
        # Fetch main JSON
        url = f"{BASE_URL}/4565.json"
        response = requests.get(url, headers=HEADERS, impersonate="chrome")
        logging.info(f"Main response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            # Extract categories 3, 4, 7 (fresh and frozen products categories)
            categories = [data[3], data[4], data[7]]
            
            for cat in categories:
                meta = {
                    'category': cat,
                    'level': 'main'
                }
                self.parse_item(cat, meta)
        else:
            logging.error(f"Failed to fetch main JSON: {response.status_code}")
    
    def parse_item(self, response, meta):
        """Parse items at all levels"""
        level = meta.get('level')
        
        if level == 'main':
            # Parse main category
            cat_id = response.get("id")
            cat_name = response.get("name")
            cat_url = response.get("url")
            logging.info(f"CATEGORY → {cat_id}: {cat_name} | {cat_url}")
            
            cat_dict = {
                "id": cat_id,
                "name": cat_name,
                "url": cat_url,
                "subcategories": []
            }
            
            subcategories = response.get("depts", [])
            
            for subcat in subcategories:
                depts = subcat.get("depts")
                sub_id = subcat.get("id")
                sub_name = subcat.get("name")
                sub_url = subcat.get("url")
                logging.info(f"  SUB-CATEGORY → {depts}|{sub_id}: {sub_name} | {sub_url}")
                
                sub_dict = {
                    "id": sub_id,
                    "name": sub_name,
                    "url": sub_url,
                    "sub_subcategories": []
                }
                
                # Build URL for sub-sub categories
                if depts:
                    next_json_url = f"{BASE_URL}/{depts}.json"
                    logging.info(f"    Fetching sub-sub categories: {next_json_url}")
                    
                    try:
                        sub_response = requests.get(next_json_url, headers=HEADERS, impersonate="chrome")
                        if sub_response.status_code == 200:
                            sub_data = sub_response.json()
                            
                            for sub_sub in sub_data:
                                sub_sub_id = sub_sub.get("id")
                                sub_sub_name = sub_sub.get("name")
                                sub_sub_url = sub_sub.get("url")
                                logging.info(f"      SUB-SUB → {sub_sub_id}: {sub_sub_name} | {sub_sub_url}")
                                
                                sub_sub_dict = {
                                    "id": sub_sub_id,
                                    "name": sub_sub_name,
                                    "url": sub_sub_url,
                                    "sub_subcategories": []
                                }
                                
                                # Handle next level depts if any
                                depts_next = sub_sub.get("depts", [])
                                for dept in depts_next:
                                    ssub_sub_id = dept.get("id")
                                    ssub_sub_name = dept.get("name")
                                    ssub_sub_url = dept.get("url")
                                    logging.info(f"        NEXT LEVEL → {ssub_sub_id}: {ssub_sub_name} | {ssub_sub_url}")
                                    
                                    sub_sub_dict["sub_subcategories"].append({
                                        "id": ssub_sub_id,
                                        "name": ssub_sub_name,
                                        "url": ssub_sub_url
                                    })
                                
                                sub_dict["sub_subcategories"].append(sub_sub_dict)
                        else:
                            logging.warning(f"Failed to fetch {next_json_url}: {sub_response.status_code}")
                    except Exception as e:
                        logging.error(f"Error fetching sub-sub categories: {e}")
                
                cat_dict["subcategories"].append(sub_dict)

            item={}
            item=cat_dict
            
            # Save to MongoDB
            try:
                self.db[MONGO_COLLECTION_CATEGORY].insert_one(item)
                logging.info(f"Inserted category: {cat_dict['name']}")
            except Exception as e:
                logging.error(f"Error saving to MongoDB: {e}")
    
    def close(self):
        """Close MongoDB connection"""
        self.mongo.close()
          


if __name__ == "__main__":
    crawler = CategoryCrawler()
    crawler.start()
    crawler.close()
