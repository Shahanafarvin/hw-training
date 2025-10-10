import json
import time
import html as html_module
from curl_cffi import requests
from lxml import html
from urllib.parse import urljoin
from settings import BASE_URL, API_URL, HEADERS, PAGE_SIZE, MONGO_URI, MONGO_DB, URLS_COLLECTION
import logging
import math
from pymongo import MongoClient, errors

class Crawler:
    """Crawler for FirstWeber Agents"""

    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[MONGO_DB]
        self.collection = self.db[URLS_COLLECTION]
        self.page = 1

    def fetch_agents(self, page_number):
        params = {
            "layoutID": 1126,
            "pageSize": PAGE_SIZE,
            "pageNumber": page_number,
            "sortBy": "firstname"
        }

        resp = requests.get(API_URL, headers=HEADERS, params=params, impersonate="chrome")
        if resp.status_code != 200:
            logging.warning(f"Failed page {page_number}: {resp.status_code}")
            return [], 0

        first_parse = json.loads(resp.text)  # decode first JSON
        data = json.loads(first_parse)       # decode actual dict

        html_content = html_module.unescape(data.get("Html", ""))
        total_count = data.get("TotalCount", 0)

        tree = html.fromstring(html_content)
        urls = tree.xpath('//a[@class="button hollow"]/@href')
        urls = [urljoin(BASE_URL, u) for u in urls]

        return urls, total_count

    def start(self):
        # Fetch first page to get total count
        urls, total_count = self.fetch_agents(self.page)
        self.save_to_mongo(urls)

        total_pages = math.ceil(total_count / PAGE_SIZE)
        logging.info(f"Total agents: {total_count}, Total pages: {total_pages}")

        # Loop remaining pages
        for page in range(2, total_pages + 1):
            logging.info(f"Fetching page {page}...")
            urls, _ = self.fetch_agents(page)
            if not urls:
                break
            self.save_to_mongo(urls)
            time.sleep(0.5)  # polite delay

    def save_to_mongo(self, urls):
        """Insert urls into MongoDB"""
        for u in urls:
            try:
                self.collection.update_one(
                    {"url": u}, {"$set": {"url": u}}, upsert=True
                )
            except errors.PyMongoError as e:
                logging.error(f"Failed to insert {u}: {e}")

        logging.info(f"Saved {len(urls)} urls to MongoDB.")

    def close(self):
        """Close MongoDB connection"""
        self.client.close()
        logging.info("Crawler finished.")

if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()
