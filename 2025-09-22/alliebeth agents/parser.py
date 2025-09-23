"""
AllieBeth Agent Profile Scraper

This module provides a comprehensive web scraper for extracting detailed information
from individual agent profile pages on the AllieBeth talent agency website. It reads
agent URLs from a MongoDB collection and scrapes detailed profile information including
personal details, contact information, office details, and social media links.

Key Features:
- Reads agent URLs from existing MongoDB collection
- Extracts comprehensive profile data from individual agent pages
- Handles missing elements gracefully with safe extraction methods
- Parses complex data like names, phone numbers, and background images
- Stores detailed profile information in separate MongoDB collection
- Prevents duplicate entries with upsert operations
- Robust error handling and logging throughout the process

Dependencies:
- undetected-chromedriver: For stealth web automation
- selenium: Web driver framework
- pymongo: MongoDB Python driver
- re: Regular expression operations for data parsing
- MongoDB server running on localhost:27017

Database Schema:
- Database: alliebeth
- Input Collection: agents (contains {"url": "agent_profile_url"})
- Output Collection: agent_profiles (contains detailed profile data)

The scraper will:
1. Connect to MongoDB and read all agent URLs from the 'agents' collection
2. Launch an undetected Chrome browser
3. Visit each agent profile page individually
4. Extract comprehensive profile information using XPath selectors
5. Parse and clean extracted data (names, phones, addresses, etc.)
6. Save detailed profile data to 'agent_profiles' collection
7. Clean up browser resources

Data Extraction Details:
- Names are intelligently parsed into first, middle, and last name components
- Phone numbers are extracted using regex patterns
- Background image URLs are parsed from CSS style attributes
- Social media links are collected from profile bio sections
- Office information and addresses are extracted from contact sections
- All extractions include error handling for missing elements

"""

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
    """
    A comprehensive web scraper for extracting detailed information from AllieBeth agent profiles.
    
    This scraper reads agent URLs from a MongoDB collection and visits each profile page to
    extract detailed information including personal details, contact information, office details,
    social media links, and profile descriptions. It handles missing elements gracefully and
    stores the extracted data in a separate MongoDB collection.
    
    Attributes:
        driver (uc.Chrome): The undetected Chrome WebDriver instance
   
    """
    def __init__(self):
        """
        Initialize the AllieBeth profile scraper.
        
        Sets up the scraper instance with a None driver that will be initialized
        when the scraping process begins.
        """
        self.driver = None

    def start_driver(self):
        """
        Initialize and start the undetected Chrome WebDriver.
        
        Configures Chrome options for optimal scraping performance and stealth.
        The browser is started in maximized mode to ensure proper element visibility
        and consistent rendering across different profile pages.
        
        Raises:
            Exception: If Chrome driver fails to start
        """
        logging.info("Starting undetected Chrome driver...")
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        self.driver = uc.Chrome(options=options)
        logging.info("Driver started.")

    def scrape_agent_profile(self, profile_url):
        """
        Extract comprehensive profile information from an individual agent page.
        
        This method navigates to an agent's profile page and extracts detailed information
        including personal details, contact information, office details, social media links,
        and profile descriptions. It uses multiple helper functions for safe data extraction
        and handles various data parsing challenges like name splitting and phone number extraction.
        
        Args:
            profile_url (str): The full URL of the agent's profile page
        
        Returns:
            dict: A comprehensive dictionary containing all extracted profile information
                with the following structure:
                - profile_url: The agent's profile URL
                - first_name: Extracted first name
                - middle_name: Extracted middle name(s) if present
                - last_name: Extracted last name
                - image_url: Agent's profile image URL
                - office_name: Name of the agent's office location
                - address: Full office address
                - description: Agent's biography/description text
                - social: List of social media profile URLs
                - mailing_url: Email contact link
                - agent_phone_numbers: Agent's direct phone number
                - office_phone_numbers: Office main phone number
        
        Note:
            The method includes several nested helper functions for safe data extraction:
            - safe_text(): Safely extracts text content with error handling
            - safe_attribute(): Safely extracts element attributes with error handling
            - get_background_image_url(): Parses CSS background-image URLs
        """
        logging.info(f"Scraping profile: {profile_url}")
        self.driver.get(profile_url)
        time.sleep(2)

        def safe_text(xpath):
            """
            Safely extract text content from an element using XPath.
            
            Args:
                xpath (str): XPath selector for the target element
            
            Returns:
                str: Cleaned text content or empty string if element not found
            """
            try:
                el = self.driver.find_element(By.XPATH, xpath)
                return el.text.strip()
            except:
                return ""

        def safe_attribute(xpath, attr):
            """
            Safely extract an attribute value from an element using XPath.
            
            Args:
                xpath (str): XPath selector for the target element
                attr (str): Name of the attribute to extract
            
            Returns:
                str: Attribute value or empty string if element/attribute not found
            """
            try:
                el = self.driver.find_element(By.XPATH, xpath)
                return el.get_attribute(attr)
            except:
                return ""
            
        def get_background_image_url(xpath):
            """
            Extract background image URL from an element's CSS style attribute.
            
            This helper function parses the CSS background-image property to extract
            the actual image URL, handling various CSS formatting including quotes
            and url() wrapper functions.
            
            Args:
                xpath (str): XPath selector for the element with background image
            
            Returns:
                str: Clean image URL or empty string if not found/parseable
            """
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
        """
        Save extracted agent profile data to MongoDB database.
        
        Uses upsert operations to prevent duplicate entries based on profile_url.
        If a profile already exists, it will be updated with the latest scraped data.
        This approach ensures that re-running the scraper won't create duplicates.
        
        Args:
            data (dict): Complete agent profile data dictionary containing all
                        extracted information including personal details, contact
                        information, and social media links
        
        Database Operation:
            - Collection: agent_profiles
            - Operation: update_one with upsert=True
            - Unique Key: profile_url
            - Action: Complete document replacement with new data
        """
        logging.info(f"Saving profile: {data.get('profile_url')}")
        profiles_col.update_one(
            {"profile_url": data.get("profile_url")},
            {"$set": data},
            upsert=True
        )

    def run(self):
        """
        Execute the complete profile scraping workflow.
        
        This is the main method that orchestrates the entire profile scraping process:
        1. Connects to MongoDB and retrieves all agent URLs from the agents collection
        2. Starts the Chrome WebDriver
        3. Iterates through each agent URL
        4. Scrapes detailed profile information from each page
        5. Saves the extracted data to the agent_profiles collection
        6. Properly cleans up browser resources
        
        The method includes comprehensive error handling to ensure the browser
        is always closed properly, even if exceptions occur during scraping.
        
        Workflow Details:
            - Reads agent URLs from the 'agents' MongoDB collection
            - Processes each URL individually to extract profile data
            - Logs progress for monitoring and debugging
            - Uses upsert operations to prevent duplicate entries
            - Ensures proper resource cleanup regardless of success/failure
        
        Raises:
            Exception: Any exception that occurs during the scraping process
                      will be logged, but the browser cleanup will still occur.
        """
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
    """
    Main execution block for the AllieBeth agent profile scraper.
    
    When run as a script, this block initializes the profile scraper and executes
    the complete workflow to extract detailed information from all agent profiles
    stored in the MongoDB agents collection.
    
    Process Overview:
    1. Reads existing agent URLs from the 'agents' MongoDB collection
    2. Visits each agent's profile page individually
    3. Extracts comprehensive profile information including:
       - Personal details (name, image, description)
       - Contact information (phones, email, address)
       - Office information and location details
       - Social media profiles and links
    4. Stores all extracted data in the 'agent_profiles' collection
    
    The scraper handles missing elements gracefully and provides detailed
    logging for monitoring progress and troubleshooting any issues.
    """
    scraper = AllieBethScraper()
    scraper.run()
