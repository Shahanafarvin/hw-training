"""
AllieBeth Agent Roster Scraper

This module provides a web scraper for extracting agent profile URLs from the AllieBeth 
talent agency website roster page. It uses undetected Chrome WebDriver to bypass 
anti-bot measures and stores the collected URLs in a MongoDB database.

Key Features:
- Bypasses Cloudflare and other anti-bot protections using undetected-chromedriver
- Implements infinite scrolling to load all available agent profiles
- Extracts agent profile URLs from the roster page
- Stores URLs in MongoDB with duplicate prevention
- Comprehensive logging for monitoring scraping progress
- Proper error handling and resource cleanup

Dependencies:
- undetected-chromedriver: For stealth web automation
- selenium: Web driver framework
- pymongo: MongoDB Python driver
- MongoDB server running on localhost:27017

Database Schema:
- Database: alliebeth
- Collection: agents
- Document Structure: {"url": "https://www.alliebeth.com/agent/profile-url"}

Usage:
    python scraper.py

The scraper will:
1. Launch an undetected Chrome browser
2. Navigate to the AllieBeth agents roster page
3. Scroll through the entire page to load all agent profiles
4. Extract all agent profile URLs
5. Save URLs to MongoDB (preventing duplicates)
6. Clean up browser resources

"""

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
    """
    A web scraper for extracting agent profile URLs from AllieBeth talent agency website.
    
    This scraper uses undetected Chrome WebDriver to navigate the AllieBeth agents roster
    page, handles infinite scrolling to load all available profiles, extracts agent URLs,
    and stores them in a MongoDB database with duplicate prevention.
    
    Attributes:
        url (str): The target URL to scrape (AllieBeth agents roster page)
        driver (uc.Chrome): The undetected Chrome WebDriver instance
        agent_urls (list): List of extracted agent profile URLs
    
    """
    def __init__(self, url):
        """
        Initialize the AllieBeth scraper with the target URL.
        
        Args:
            url (str): The URL of the AllieBeth agents roster page to scrape
        """
        self.url = url
        self.driver = None
        self.agent_urls = []

    def start_driver(self):
        """
        Initialize and start the undetected Chrome WebDriver.
        
        Configures Chrome options for optimal scraping performance and stealth.
        The browser is started in maximized mode to ensure proper element visibility.
        
        Raises:
            Exception: If Chrome driver fails to start
        """
        logging.info("Starting undetected Chrome driver...")
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        self.driver = uc.Chrome(options=options)
        logging.info("Driver started.")

    def open_page(self):
        """
        Navigate to the target URL and wait for initial page load.
        
        Includes a 5-second wait to allow Cloudflare protection and dynamic
        content to fully load before proceeding with scraping operations.
        """
        logging.info(f"Opening page: {self.url}")
        self.driver.get(self.url)
        time.sleep(5)  # Wait for Cloudflare / initial load
        logging.info("Page loaded.")

    def scroll_to_load_agents(self, pause_time=2):
        """
        Perform infinite scrolling to load all available agent profiles.
        
        The AllieBeth roster page uses lazy loading, so this method continuously
        scrolls to the bottom of the page until no new content is loaded,
        ensuring all agent profiles are available for extraction.
        
        Args:
            pause_time (int, optional): Time in seconds to wait between scroll
                                      attempts. Defaults to 2 seconds.
        
        Note:
            The method compares page heights before and after scrolling to
            determine when all content has been loaded.
        """
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
        """
        Extract all agent profile URLs from the loaded page.
        
        Searches for all anchor elements with the CSS class 'site-roster-card-image-link'
        which contain the links to individual agent profile pages. The extracted URLs
        are stored in the agent_urls attribute.
        
        Note:
            The XPath selector targets the specific CSS class used by AllieBeth
            for agent profile links in their roster card layout.
        """
        logging.info("Extracting agent URLs...")
        agent_elements = self.driver.find_elements(
            By.XPATH, "//a[contains(@class, 'site-roster-card-image-link')]"
        )
        self.agent_urls = [el.get_attribute("href") for el in agent_elements]
        logging.info(f"Total agents found: {len(self.agent_urls)}")

    def save_to_mongodb(self):
        """
        Save extracted agent URLs to MongoDB database.
        
        Uses upsert operations to prevent duplicate entries. Each URL is stored
        as a document with the URL as both the unique identifier and the data field.
        This approach ensures that running the scraper multiple times won't create
        duplicate records.
        
        Database Structure:
            - Database: alliebeth
            - Collection: agents
            - Document: {"url": "agent_profile_url"}
        
        Note:
            The update_one operation with upsert=True will insert new URLs
            or update existing ones, effectively preventing duplicates.
        """
        logging.info("Saving agent URLs to MongoDB...")
        for url in self.agent_urls:
            collection.update_one(
                {"url": url},  # unique key
                {"$set": {"url": url}},
                upsert=True
            )
        logging.info("Data saved to MongoDB.")

    def close_driver(self):
        """
        Properly close and clean up the Chrome WebDriver instance.
        
        This method ensures that browser resources are properly released
        and prevents memory leaks or zombie browser processes.
        """
        logging.info("Closing driver...")
        self.driver.quit()
        logging.info("Driver closed.")

    def run(self):
        """
        Execute the complete scraping workflow.
        
        This is the main method that orchestrates the entire scraping process:
        1. Starts the Chrome WebDriver
        2. Opens the target page
        3. Scrolls to load all content
        4. Extracts agent URLs
        5. Saves data to MongoDB
        6. Cleans up resources (even if errors occur)
        
        The method includes proper error handling to ensure the browser
        is always closed, even if an exception occurs during scraping.
        
        Raises:
            Exception: Any exception that occurs during the scraping process
                      will be logged, but the browser cleanup will still occur.
        """
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
    """
    Main execution block for the AllieBeth agent scraper.
    
    When run as a script, this block initializes the scraper with the
    AllieBeth agents roster URL and executes the complete scraping workflow.
    
    The scraper will extract all agent profile URLs from the roster page
    and store them in the MongoDB database for further processing.
    """
    url = "https://www.alliebeth.com/roster/Agents"
    scraper = AllieBethScraper(url)
    scraper.run()
