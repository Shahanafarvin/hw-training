import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import logging
from pymongo import MongoClient
import re

# ----------------- Logging Setup -----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ----------------- MongoDB Setup -----------------
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "alliebeth"
AGENT_COLLECTION = "agents"          # already contains URLs
PROFILE_COLLECTION = "agent_profiles"  # new collection for scraped data

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
agents_col = db[AGENT_COLLECTION]
profiles_col = db[PROFILE_COLLECTION]


# ----------------- Scraper Class -----------------
class AllieBethScraper:
    def __init__(self):
        self.driver = None

    def start_driver(self):
        logging.info("Starting undetected Chrome driver...")
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        self.driver = uc.Chrome(options=options)
        logging.info("Driver started.")

    def scrape_agent_profile(self, profile_url):
        logging.info(f"Scraping profile: {profile_url}")
        self.driver.get(profile_url)
        time.sleep(2)

        def safe_text(xpath):
            try:
                el = self.driver.find_element(By.XPATH, xpath)
                return el.text.strip()
            except:
                return ""

        def safe_attribute(xpath, attr):
            try:
                el = self.driver.find_element(By.XPATH, xpath)
                return el.get_attribute(attr)
            except:
                return ""
            
        def get_background_image_url(xpath):
            try:
                style = self.driver.find_element(By.XPATH, xpath).get_attribute("style")
                return style.split("url(")[-1].split(")")[0].strip().strip('"').strip("'")
            except:
                return ""

        # --- Extract name ---
        full_name = safe_text("//div[contains(@class,'site-info-contact')]/h2")
        name_parts = full_name.split()
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        middle_name = " ".join(name_parts[1:-1]) if len(name_parts) > 2 else ""
        last_name = name_parts[-1] if len(name_parts) > 1 else ""

        # --- Office name ---
        office_name = safe_text("//div[@class='site-info-contact']//p/b")

        # --- Address ---
        address = safe_text("//div[@class='site-info-contact']//p[./b]")

        # --- Phones ---
        agent_phone = safe_text("//div[@class='site-info-contact']//p[a[contains(@href,'tel:')]]/a")
        office_phone_text = safe_text("//div[@class='site-info-contact']//p[contains(., 'Office Phone')]")
        # extract phone number with regex
        office_phone_match = re.search(r"Office Phone:\s*([\(\)\d\-\s]+)", office_phone_text)
        office_phone = office_phone_match.group(1).strip() if office_phone_match else ""
        

        # --- Social links ---
        social_links = [
            el.get_attribute("href")
            for el in self.driver.find_elements(By.XPATH, "//ul[@class='no-bullet site-bio-social']//a")
        ]

        agent_data = {
            "profile_url": profile_url,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "image_url": get_background_image_url("//div[contains(@class,'site-bio-image')]"),
            "office_name": office_name,
            "address": address,
            "description": safe_text("//div[@class='site-about-column']//div"),
            "social": social_links,
            "mailing_url": safe_attribute("//ul[@class='no-bullet site-info-contact-icons']//a", "href"),
            "agent_phone_numbers": agent_phone,
            "office_phone_numbers": office_phone,
        }
        return agent_data

    def save_to_mongodb(self, data):
        logging.info(f"Saving profile: {data.get('profile_url')}")
        profiles_col.update_one(
            {"profile_url": data.get("profile_url")},
            {"$set": data},
            upsert=True
        )

    def run(self):
        self.start_driver()
        try:
            # read all agent URLs from DB
            urls = [doc["url"] for doc in agents_col.find({}, {"url": 1})]
            logging.info(f"Found {len(urls)} agent URLs in MongoDB")

            for url in urls:
                profile_data = self.scrape_agent_profile(url)
                self.save_to_mongodb(profile_data)

        finally:
            self.driver.quit()
            logging.info("Scraping finished.")


# ----------------- Main -----------------
if __name__ == "__main__":
    scraper = AllieBethScraper()
    scraper.run()
