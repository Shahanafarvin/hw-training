"""
Lulu Hypermarket Product Scraper

This module scrapes individual product details from Lulu Hypermarket using Playwright
and stores them in MongoDB. It extracts product information like title, price, 
description, availability, and images from product pages.

The scraper reads from a MongoDB collection containing categories and product URLs,
then scrapes each product page and saves the details to a separate products collection.

Dependencies:
    - playwright
    - pymongo
    - logging (built-in)
    - random (built-in) 
    - time (built-in)

Database Collections:
    - Input: categories_with_products (contains product URLs to scrape)
    - Output: products (stores scraped product details)

"""
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
    """
    A web scraper class for extracting product details from Lulu Hypermarket.
    
    This class handles the complete workflow of:
    1. Connecting to MongoDB to read product URLs
    2. Launching Playwright browser with user agent rotation
    3. Scraping individual product pages for details
    4. Storing extracted product data back to MongoDB
    
    Attributes:
        mongo_uri (str): MongoDB connection string
        db_name (str): Name of the MongoDB database
        user_agents (list): List of user agent strings for rotation
        headless (bool): Whether to run browser in headless mode
        client (MongoClient): MongoDB client instance
        db (Database): MongoDB database instance
        final_collection (Collection): Collection containing product URLs
        products_collection (Collection): Collection for storing product details
    """
    def __init__(self, mongo_uri, db_name, user_agents_file, headless=False):
        """
        Initialize the LuluProductScraper with database connection and configuration.
        
        Args:
            mongo_uri (str): MongoDB connection URI
            db_name (str): Name of the MongoDB database to use
            user_agents_file (str): Path to file containing user agent strings
            headless (bool, optional): Run browser in headless mode. Defaults to False.
            
        Raises:
            mongo_errors.PyMongoError: If MongoDB connection fails
            Exception: If user agents file cannot be loaded
        """
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
        """
        Load user agent strings from a text file.
        
        Args:
            filepath (str): Path to the user agents text file
            
        Returns:
            list: List of user agent strings (empty lines filtered out)
            
        Raises:
            Exception: If file cannot be read or parsed
        """
        try:
            with open(filepath, "r") as f:
                agents = [line.strip() for line in f if line.strip()]
            logging.info(f"Loaded {len(agents)} user agents.")
            return agents
        except Exception as e:
            logging.error(f"Failed to load user agents: {e}")
            raise

    def _get_random_ua(self):
        """
        Get a random user agent string from the loaded list.
        
        Returns:
            str: Random user agent string
        """
        return random.choice(self.user_agents)

    def scrape_product(self, browser, product_url, main_category, subcategory_url):
        """
        Scrape details for a single product page.
        
        Extracts product information including title, price, description,
        availability, and images from a Lulu Hypermarket product page.
        
        Args:
            browser: Playwright browser instance
            product_url (str): URL of the product page to scrape
            main_category (str): Main category URL this product belongs to
            subcategory_url (str): Subcategory URL this product belongs to
            
        Returns:
            dict: Dictionary containing scraped product data with keys:
                - main_category (str): Main category URL
                - subcategory_url (str): Subcategory URL  
                - product_url (str): Product page URL
                - title (str): Product title/name
                - price (str): Product price
                - description (list): List of product description points
                - availability (str): Product availability/brand info
                - images (list): List of product image URLs
        """
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
        """
        Execute the main scraping workflow.
        
        This method:
        1. Launches a Playwright browser instance
        2. Reads all categories and product URLs from MongoDB
        3. Iterates through each product URL and scrapes its details
        4. Saves scraped product data to MongoDB products collection
        5. Includes anti-bot delays and proper cleanup
        
        The method processes all documents in the categories_with_products collection,
        extracting product URLs and scraping each one individually.
        
        Raises:
            mongo_errors.PyMongoError: If database operations fail
            PlaywrightTimeoutError: If browser operations timeout
            Exception: For other scraping errors
        """
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
    """
    Entry point of the script.
    
    Initializes and runs the LuluProductScraper with default configuration
    when the script is executed directly.
    """
    scraper = LuluProductScraper(
        mongo_uri="mongodb://localhost:27017/",
        db_name="lulu_hypermarket",
        user_agents_file="/home/shahana/datahut-training/hw-training/2025-09-17/lulu hypermarket/user_agents.txt",
        headless=False
    )
    scraper.run()
