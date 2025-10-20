# crawler.py
import logging
import requests
from settings import HEADERS, API_ENDPOINT, BASE_URL, MONGO_COLLECTION_URL, MONGO_DB
from items import PropertyUrl


class Crawler:
    """Crawling property URLs from Baity"""

    def __init__(self):
        # MongoDB connection
        self.db = self.client[MONGO_DB]
        self.collection = self.db[MONGO_COLLECTION_URL]

    def start(self):
        """Start crawling all pages"""
        page = 1
        total_count = 0
        logging.info("Starting crawl...")

        while True:
            api_url = API_ENDPOINT.format(page=page)
            logging.info(f"Fetching page {page} → {api_url}")

            try:
                response = requests.get(api_url, headers=HEADERS, timeout=30)
            except Exception as e:
                logging.error(f"Request failed for page {page}: {e}")
                break

            if response.status_code != 200:
                logging.warning(f"Page {page} returned status {response.status_code}")
                break

            data = response.json()
            props = data.get("properties", {}).get("data", [])
            last_page = data.get("properties", {}).get("last_page", page)

            if not props:
                logging.info("No properties found, ending crawl.")
                break

            page_count = 0
            for prop in props:
                try:
                    item = {
                        "id": prop.get("id"),
                        "url": f"{BASE_URL}{prop.get('slug', '')}" if prop.get("slug") else "",
                        "title": prop.get("title") or prop.get("name") or "",
                        "price": prop.get("price"),
                        "agency_name": prop.get("agency", {}).get("name"),
                        "agency_contact_number": prop.get("agency", {}).get("agency_contact_number"),
                        "governorate": prop.get("governorate", {}).get("name"),
                        "area": prop.get("area", {}).get("name"),
                        "images": prop.get("images", []),
                        "property_size": prop.get("plot_area"),
                        "rate_per_sqft": prop.get("eb_rate"),
                        "property_type": prop.get("property_type"),
                        "rooms":prop.get("beds"),
                        "bathrooms":prop.get("baths"),
                        "roads":prop.get("land_road"),
                        "parking":prop.get("parking"),
                        "built_up_area":prop.get("built_up_area"),
                        "classification":prop.get("classification"),

                    }

                    PropertyUrl.objects(url=item["url"]).modify(upsert=True, new=True, **item)
                    page_count += 1
                    total_count += 1

                except Exception as e:
                    logging.error(f"Error parsing property item: {e}")
                    continue

            logging.info(f"Page {page}: {page_count} properties saved (Total so far: {total_count})")

            if page >= last_page:
                logging.info(f" All {total_count} properties crawled successfully.")
                break

            page += 1

    def close(self):
        """Close MongoDB connection"""
        self.client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    crawler = Crawler()
    crawler.start()
    crawler.close()
