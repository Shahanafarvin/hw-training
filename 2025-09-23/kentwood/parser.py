import time
import logging
from typing import Dict
from pymongo import MongoClient
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By


# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("agent_details_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AgentDetailsScraper:
    def __init__(self, mongo_uri: str, db_name: str, source_collection: str, target_collection: str):
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.source_collection = source_collection
        self.target_collection = target_collection
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

    def _extract_text(self, xpath: str) -> str:
        """Helper to safely extract element text."""
        try:
            return self.driver.find_element(By.XPATH, xpath).text.strip()
        except Exception:
            return None

    def _extract_attr(self, xpath: str, attr: str) -> str:
        """Helper to safely extract element attribute."""
        try:
            return self.driver.find_element(By.XPATH, xpath).get_attribute(attr)
        except Exception:
            return None

    def _extract_agent_details(self, url: str) -> Dict:
        """Extract details from an agent profile page."""
        logger.info(f"Visiting {url}")
        self.driver.get(url)
        time.sleep(3)  # allow page to load

        details = {
            "profile_url": url,
            "first_name": "",
            "middle_name": "",
            "last_name": "",
            "image_url": "",
            "office_name": "",
            "address": "",
            "description": "",
            "languages": [],
            "social": [],
            "website": "",
            "email": "",
            "title": "",
            "country": "USA",
            "city": "",
            "zipcode": "",
            "state": "",
            "agent_phone_numbers":"",
            "office_phone_numbers": "",
        }

        try:
           
            p_elem = self.driver.find_element(By.XPATH, "//p[@class='rng-agent-profile-contact-name']")

            # Extract name only (exclude <span>)
            full_name = p_elem.get_attribute("innerText").split("\n")[0].strip()
            if full_name:
                parts = full_name.split()
                if len(parts) >= 1: details["first_name"] = parts[0]
                if len(parts) == 2: details["last_name"] = parts[1]
                if len(parts) > 2:
                    details["middle_name"] = " ".join(parts[1:-1])
                    details["last_name"] = parts[-1]

            details["title"] = self._extract_text("//span[@class='rng-agent-profile-contact-title']")

            details["image_url"] = self._extract_attr("//img[contains(@class,'rng-agent-profile-photo')]", "src")

            details["email"] = self._extract_attr("//li[@class='rng-agent-profile-contact-email']/a", "href")
            if details["email"]:
                details["email"] = "https://www.kentwood.com/" + details["email"]

            # Phones
            agent_phones = self.driver.find_elements(By.XPATH, "//li[@class='rng-agent-profile-contact-phone']/a")
            details["agent_phone_numbers"] = agent_phones[0].text.strip() if agent_phones else ""

            # address
            full_address= self._extract_text("//li[@class='rng-agent-profile-contact-address']")
            lines = [line.strip() for line in full_address.split("\n") if line.strip()]
            
            if len(lines) >= 2:
                details["address"] = lines[0]
                city_state_zip = lines[1].split()
                if len(city_state_zip) > 3:
                    details["city"] = " ".join(city_state_zip[:-2])
                    details["state"] = city_state_zip[-2]
                    details["zipcode"] = city_state_zip[-1]
                elif len(city_state_zip) == 3:
                    details["city"] = city_state_zip[0]
                    details["state"] = city_state_zip[1]
                    details["zipcode"] = city_state_zip[2]

            # Description / Bio
            details["description"] = self._extract_text("//div[contains(@id,'widget-text-1-preview-')]")

            # Social media links
            socials = self.driver.find_elements(By.XPATH, "//li[contains(@class,'social-')]/a")
            details["social"] = [el.get_attribute("href") for el in socials if el.get_attribute("href")]

            # Website
            details["website"] = self._extract_attr("//li[@class='rng-agent-profile-contact-website']/a", "href")

        except Exception as e:
            logger.exception(f"Error extracting details for {url}: {e}")

        return details

    def run(self, limit: int = 0):
        """Main runner to fetch links from Mongo and save details."""
        try:
            logger.info("Connecting to MongoDB...")
            client = MongoClient(self.mongo_uri)
            db = client[self.db_name]
            src_coll = db[self.source_collection]
            tgt_coll = db[self.target_collection]

            urls = list(src_coll.find({}, {"url": 1, "_id": 0}))
            urls = [u["url"] for u in urls]

            if limit > 0:
                urls = urls[:limit]

            logger.info(f"Found {len(urls)} URLs to process.")

            self._launch_browser()

            for url in urls:
                details = self._extract_agent_details(url)

                tgt_coll.update_one(
                    {"profile_url": url},
                    {"$set": details},
                    upsert=True
                )
                logger.info(f"Saved details for {url}")

        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
        finally:
            self._close_browser()


if __name__ == "__main__":
    # --- Config ---
    mongo_uri = "mongodb://localhost:27017"
    db_name = "kentwood_agents"
    source_collection = "agent_links"       # links scraped earlier
    target_collection = "agent_details"     # save structured details

    scraper = AgentDetailsScraper(mongo_uri, db_name, source_collection, target_collection)
    scraper.run()  
