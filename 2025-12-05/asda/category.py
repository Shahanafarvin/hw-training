from curl_cffi import requests
from pymongo import MongoClient
from settings import logging, BASE_URL, HEADERS, MONGO_DB, MONGO_COLLECTION_CATEGORY

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
        
        if response.status_code == 200:
            categories = response.json()
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
                
                sub_dict = {
                    "id": sub_id,
                    "name": sub_name,
                    "url": sub_url,
                    "sub_subcategories": []
                }
                
                # Build URL for sub-sub categories
                if depts:
                    next_json_url = f"{BASE_URL}/{depts}.json"
                    
                    try:
                        sub_response = requests.get(next_json_url, headers=HEADERS, impersonate="chrome")
                        if sub_response.status_code == 200:
                            sub_data = sub_response.json()
                            
                            for sub_sub in sub_data:
                                sub_sub_id = sub_sub.get("id")
                                sub_sub_name = sub_sub.get("name")
                                sub_sub_url = sub_sub.get("url")
                                
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

            logging.info(item)
            # Save to MongoDB
            try:
                self.db[MONGO_COLLECTION_CATEGORY].insert_one(item)
                
            except Exception as e:
                logging.error(f"Error saving to MongoDB: {e}")
    
    def close(self):
        """Close MongoDB connection"""
        self.mongo.close()
          

if __name__ == "__main__":
    crawler = CategoryCrawler()
    crawler.start()
    crawler.close()
