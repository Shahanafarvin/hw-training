import time
import logging
from typing import List
from pymongo import MongoClient
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By


# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("agents_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AgentScraper:
    def __init__(self, url: str, mongo_uri: str, db_name: str, collection: str):
        self.url = url
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection
        self.links: List[str] = []
        self.driver = None

    def _launch_browser(self):
        """Launch undetected Chrome browser."""
        logger.info("Launching undetected Chrome...")
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-gpu")
        options.add_argument("--start-maximized")

        self.driver = uc.Chrome(options=options)
        logger.info("Browser launched successfully.")

    def _close_browser(self):
        """Close browser."""
        if self.driver:
            logger.info("Closing browser...")
            self.driver.quit()

    def _scroll_part_by_part(self, pause: float = 2.0, step: int = 1000):
        """Scroll down the page in increments until the end is reached."""
        logger.info("Scrolling part by part to load all agents...")
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        position = 0

        while True:
            position += step
            self.driver.execute_script(f"window.scrollTo(0, {position});")
            time.sleep(pause)

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            logger.debug(f"Scrolled to {position}px / page height = {new_height}")

            if position >= new_height:
                logger.info("Reached bottom of the page, no more content to load.")
                break
            last_height = new_height

    def fetch_links(self, xpath: str):
        """Fetch agent links using provided XPath after full scroll."""
        try:
            self._launch_browser()
            logger.info(f"Navigating to {self.url}")
            self.driver.get(self.url)
            time.sleep(5)  # Let page load fully

            # Scroll in parts
            self._scroll_part_by_part()

            logger.info("Extracting agent links...")
            elements = self.driver.find_elements(By.XPATH, xpath)

            for el in elements:
                href = el.get_attribute("href")
                if href and href not in self.links:
                    self.links.append(href)
                    logger.debug(f"Extracted link: {href}")

            logger.info(f"Total {len(self.links)} links extracted.")

        except Exception as e:
            logger.exception(f"Error fetching agent links: {e}")
        finally:
            self._close_browser()

    def save_to_mongo(self):
        """Save links to MongoDB with upsert to avoid duplicates."""
        if not self.links:
            logger.warning("No links to save into MongoDB.")
            return

        try:
            logger.info("Connecting to MongoDB...")
            client = MongoClient(self.mongo_uri)
            db = client[self.db_name]
            coll = db[self.collection_name]

            inserted_count = 0
            for link in self.links:
                result = coll.update_one(
                    {"url": link},
                    {"$setOnInsert": {"url": link}},
                    upsert=True
                )
                if result.upserted_id:
                    inserted_count += 1
                    logger.debug(f"Inserted new link: {link}")

            logger.info(f"Saved {inserted_count} new links into MongoDB.")

        except Exception as e:
            logger.exception(f"Error saving to MongoDB: {e}")


if __name__ == "__main__":
    # --- Config ---
    roster_url = "https://www.kentwood.com/roster/agents/"
    xpath_expr = "//a[@class='btn btn-outline-primary button hollow']"  
    mongo_uri = "mongodb://localhost:27017"
    db_name = "kentwood_agents"
    collection_name = "agent_links"

    scraper = AgentScraper(roster_url, mongo_uri, db_name, collection_name)
    scraper.fetch_links(xpath_expr)
    scraper.save_to_mongo()
