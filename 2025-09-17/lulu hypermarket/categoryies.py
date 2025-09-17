from playwright.sync_api import sync_playwright
import random
import time
from pymongo import MongoClient

# Load user agents from file
with open("/home/shahana/datahut-training/hw-training/2025-09-17/lulu hypermarket/user_agents.txt", "r") as f:
    user_agents = [line.strip() for line in f if line.strip()]

# List of main category URLs
category_urls = [
    "https://gcc.luluhypermarket.com/en-ae/grocery/",
    "https://gcc.luluhypermarket.com/en-ae/fresh-food/",
    "https://gcc.luluhypermarket.com/en-ae/electronics/",
    "https://gcc.luluhypermarket.com/en-ae/home-living/"
]

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["lulu_hypermarket"]
subcategory_collection = db["subcategories"]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    
    for url in category_urls:
        # Rotate user agent
        ua = random.choice(user_agents)
        context = browser.new_context(extra_http_headers={"user-agent": ua})
        page = context.new_page()
        
        print(f"Visiting main category: {url} with UA: {ua}")
        
        try:
            time.sleep(random.uniform(2, 5))  # Random delay
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            
            # Wait for subcategory elements
            page.wait_for_selector("a.flex.flex-shrink-0.flex-col.items-center.justify-start.gap-1")
            
            # Extract subcategory links
            sub_links = page.eval_on_selector_all(
                "a.flex.flex-shrink-0.flex-col.items-center.justify-start.gap-1",
                "elements => elements.map(el => el.href)"
            )
            
            print(f"Found {len(sub_links)} subcategories for {url}")
            
            # Save main category + subcategories as one document
            document = {
                "main_category": url,
                "subcategories": sub_links
            }
            subcategory_collection.update_one(
                {"main_category": url},  # filter
                {"$set": document},      # update
                upsert=True              # insert if not exists
            )
            print(f"Saved {url} with {len(sub_links)} subcategories")
        
        except Exception as e:
            print(f"Error visiting main category {url}: {e}")
        
        finally:
            context.close()
    
    browser.close()
    client.close()
