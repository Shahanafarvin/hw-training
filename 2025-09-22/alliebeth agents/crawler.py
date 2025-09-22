import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import logging
from pymongo import MongoClient

# ----------------- Logging Setup -----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ----------------- MongoDB Setup -----------------
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "alliebeth"
COLLECTION_NAME = "agents"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# ----------------- Scraper Class -----------------
class AllieBethScraper:
    def __init__(self, url):
        self.url = url
        self.driver = None
        self.agent_urls = []

    def start_driver(self):
        logging.info("Starting undetected Chrome driver...")
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        self.driver = uc.Chrome(options=options)
        logging.info("Driver started.")

    def open_page(self):
        logging.info(f"Opening page: {self.url}")
        self.driver.get(self.url)
        time.sleep(5)  # Wait for Cloudflare / initial load
        logging.info("Page loaded.")

    def scroll_to_load_agents(self, pause_time=2):
        logging.info("Scrolling to load all agents...")
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(pause_time)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                logging.info("Reached bottom of page. All agents loaded.")
                break
            last_height = new_height
            logging.info("New content loaded, continuing scrolling...")

    def extract_agent_urls(self):
        logging.info("Extracting agent URLs...")
        agent_elements = self.driver.find_elements(
            By.XPATH, "//a[contains(@class, 'site-roster-card-image-link')]"
        )
        self.agent_urls = [el.get_attribute("href") for el in agent_elements]
        logging.info(f"Total agents found: {len(self.agent_urls)}")

    def save_to_mongodb(self):
        logging.info("Saving agent URLs to MongoDB...")
        for url in self.agent_urls:
            collection.update_one(
                {"url": url},  # unique key
                {"$set": {"url": url}},
                upsert=True
            )
        logging.info("Data saved to MongoDB.")

    def close_driver(self):
        logging.info("Closing driver...")
        self.driver.quit()
        logging.info("Driver closed.")

    def run(self):
        self.start_driver()
        try:
            self.open_page()
            self.scroll_to_load_agents()
            self.extract_agent_urls()
            self.save_to_mongodb()
        finally:
            self.close_driver()


# ----------------- Main -----------------
if __name__ == "__main__":
    url = "https://www.alliebeth.com/roster/Agents"
    scraper = AllieBethScraper(url)
    scraper.run()
