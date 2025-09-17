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


class LuluProductScraper:
    def __init__(self, mongo_uri, db_name, user_agents_file, headless=False):
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.user_agents = self._load_user_agents(user_agents_file)
        self.headless = headless

        # MongoDB connection
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.db_name]
            self.final_collection = self.db["categories_with_products"]
            self.products_collection = self.db["products"]
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

    def scrape_product(self, browser, product_url, main_category, subcategory_url):
        """Scrape details for a single product."""
        ua = self._get_random_ua()
        context = browser.new_context(extra_http_headers={"user-agent": ua})
        page = context.new_page()

        logging.info(f"Scraping product: {product_url} (Category: {main_category})")

        product_data = {
            "main_category": main_category,
            "subcategory_url": subcategory_url,
            "product_url": product_url
        }

        try:
            page.goto(product_url, timeout=60000, wait_until="domcontentloaded")
            time.sleep(random.uniform(2, 4))

            # Title
            try:
                tittle_el=page.query_selector('//h1[@data-testid="product-name"]')
                product_data["title"] = tittle_el.inner_text().strip() if tittle_el else ""
            except Exception:
                product_data["title"] = ""

            # Price
            try:
                price_el = page.query_selector("//span[@data-testid='price']")
                product_data["price"] = price_el.inner_text().strip() if price_el else ""
            except Exception:
                product_data["price"] = ""

            # Description
            try:
                desc_el = page.query_selector_all("//li[@class='flex gap-3.5 text-sm text-gray-620']//span")
                product_data["description"] = [el.inner_text().strip() for el in desc_el if desc_el]
            except Exception:
                product_data["description"] = []

            # Availability / Stock
            try:
                brand_el = page.query_selector("//a[@class='whitespace-nowrap text-primary']")
                product_data["availability"] = brand_el.inner_text().strip() if brand_el else ""
            except Exception:
                product_data["availability"] = ""

            # Images
            try:
                img_elements = page.query_selector_all("//div[contains(@class,'swiper-wrapper')]//img")
                product_data["images"] = [img.get_attribute("src") for img in img_elements if img.get_attribute("src")]
            except Exception:
                product_data["images"] = []

        except PlaywrightTimeoutError:
            logging.error(f"Timeout loading {product_url}")
        except Exception as e:
            logging.error(f"Error scraping {product_url}: {e}")
        finally:
            context.close()

        return product_data

    def run(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)

            # Iterate over all categories and products
            for doc in self.final_collection.find():
                main_category = doc["main_category"]
                subcategories = doc.get("subcategories", [])

                for sub in subcategories:
                    subcategory_url = sub["subcategory_url"]
                    product_urls = sub.get("products", [])

                    for product_url in product_urls:
                        product_data = self.scrape_product(browser, product_url, main_category, subcategory_url)

                        try:
                            self.products_collection.update_one(
                                {"product_url": product_url},
                                {"$set": product_data},
                                upsert=True
                            )
                            logging.info(f"Saved product: {product_data.get('title')}")
                        except mongo_errors.PyMongoError as e:
                            logging.error(f"Failed to save product {product_url}: {e}")

                        time.sleep(random.uniform(2, 5))  # anti-bot delay

            browser.close()
            self.client.close()
            logging.info("Product scraping completed and MongoDB connection closed.")


if __name__ == "__main__":
    scraper = LuluProductScraper(
        mongo_uri="mongodb://localhost:27017/",
        db_name="lulu_hypermarket",
        user_agents_file="/home/shahana/datahut-training/hw-training/2025-09-17/lulu hypermarket/user_agents.txt",
        headless=False
    )
    scraper.run()
