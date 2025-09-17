import logging
import random
import time
from pymongo import MongoClient, errors as mongo_errors
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ------------------------------
# Logging setup
# ------------------------------
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


class LuluScraper:
    def __init__(self, mongo_uri, db_name, user_agents_file, headless=False):
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.user_agents = self._load_user_agents(user_agents_file)
        self.headless = headless

        # MongoDB connection
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.db_name]
            self.subcategory_collection = self.db["subcategories"]
            self.final_collection = self.db["categories_with_products"]
            logging.info("Connected to MongoDB successfully.")
        except mongo_errors.PyMongoError as e:
            logging.error(f"MongoDB connection failed: {e}")
            raise

    def _load_user_agents(self, filepath):
        try:
            with open(filepath, "r") as f:
                agents = [line.strip() for line in f if line.strip()]
            logging.info(f"Loaded {len(agents)} user agents.")
            return agents
        except Exception as e:
            logging.error(f"Failed to load user agents: {e}")
            raise

    def _get_random_ua(self):
        return random.choice(self.user_agents)

    def _get_last_page(self, page):
        """Extracts last page number from pagination."""
        try:
            pagination_numbers = page.query_selector_all("//a[contains(@class,'px-2 text-xs')]")
            if pagination_numbers:
                return max([int(el.inner_text()) for el in pagination_numbers if el.inner_text().isdigit()])
            return 1
        except Exception:
            return 1

    def scrape_subcategory(self, playwright, browser, sub_url, main_category):
        """Scrape products for a single subcategory (all pages)."""
        product_urls = []
        ua = self._get_random_ua()
        context = browser.new_context(extra_http_headers={"user-agent": ua})
        page = context.new_page()

        logging.info(f"Visiting subcategory: {sub_url} (Main: {main_category}) with UA: {ua}")

        try:
            page.goto(sub_url, timeout=60000, wait_until="domcontentloaded")
            time.sleep(random.uniform(2, 5))

            last_page = self._get_last_page(page)
            logging.info(f"Found {last_page} pages for {sub_url}")

            # Loop over all pages
            for page_num in range(1, last_page + 1):
                paginated_url = f"{sub_url}?page={page_num}"
                logging.info(f"Fetching {paginated_url}")

                ua = self._get_random_ua()
                context2 = browser.new_context(extra_http_headers={"user-agent": ua})
                page2 = context2.new_page()

                try:
                    page2.goto(paginated_url, timeout=60000, wait_until="domcontentloaded")
                    page2.wait_for_selector("//a[contains(@class,'relative z-0 flex flex-col')]", timeout=10000)

                    product_links = page2.eval_on_selector_all(
                        "//a[contains(@class,'relative z-0 flex flex-col')]",
                        "elements => elements.map(el => el.href)"
                    )
                    product_urls.extend(product_links)
                    logging.info(f"Collected {len(product_links)} products from {paginated_url}")

                except PlaywrightTimeoutError:
                    logging.warning(f"No products found on {paginated_url} (timeout). Stopping pagination.")
                    break
                except Exception as e:
                    logging.error(f"Error loading {paginated_url}: {e}")
                finally:
                    context2.close()
                    time.sleep(random.uniform(2, 4))

        except Exception as e:
            logging.error(f"Error visiting subcategory {sub_url}: {e}")
        finally:
            context.close()

        return {
            "subcategory_url": sub_url,
            "products": list(set(product_urls))  # deduplicate
        }

    def run(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)

            for doc in self.subcategory_collection.find():
                main_category = doc["main_category"]
                subcategories = doc.get("subcategories", [])

                nested_subcategories = []

                for sub_url in subcategories:
                    data = self.scrape_subcategory(p, browser, sub_url, main_category)
                    nested_subcategories.append(data)

                try:
                    self.final_collection.update_one(
                        {"main_category": main_category},
                        {"$set": {"main_category": main_category, "subcategories": nested_subcategories}},
                        upsert=True
                    )
                    logging.info(f"Saved {len(nested_subcategories)} subcategories with products for {main_category}")
                except mongo_errors.PyMongoError as e:
                    logging.error(f"Failed to save data for {main_category}: {e}")

            browser.close()
            self.client.close()
            logging.info("Scraping finished and MongoDB connection closed.")


if __name__ == "__main__":
    scraper = LuluScraper(
        mongo_uri="mongodb://localhost:27017/",
        db_name="lulu_hypermarket",
        user_agents_file="/home/shahana/datahut-training/hw-training/2025-09-17/lulu hypermarket/user_agents.txt",
        headless=False
    )
    scraper.run()
