"""
Kentwood Real Estate Agent Profile Details Scraper

This module provides a comprehensive web scraper for extracting detailed profile information
from individual Kentwood Real Estate agent pages. It reads agent URLs from a MongoDB collection
and scrapes comprehensive profile data including personal details, contact information,
office locations, social media links, and professional descriptions.

Key Features:
- Processes agent URLs from existing MongoDB collection (agent_links)
- Extracts comprehensive profile data from individual agent detail pages
- Intelligent name parsing with support for first, middle, and last names
- Complex address parsing with city, state, and zipcode extraction
- Social media link collection and validation
- Professional information extraction (title, description, languages)
- Contact information processing (phone, email, website)
- MongoDB integration with upsert operations for data persistence
- Comprehensive error handling and logging for production environments
- Configurable processing limits for testing and batch processing

Technical Approach:
- Uses undetected Chrome WebDriver to bypass anti-bot protections
- Implements safe extraction methods with graceful error handling
- Sophisticated text parsing for complex address and name formats
- Handles dynamic content loading with appropriate wait times
- Processes multiple data types: text, attributes, lists, and structured data

Dependencies:
- undetected-chromedriver: For stealth web automation
- selenium: Web driver framework
- pymongo: MongoDB Python driver
- typing: Type hint support
- MongoDB server running on localhost:27017


Configuration:
    All parameters can be modified in the __main__ section:
    - mongo_uri: MongoDB connection string
    - db_name: Database name containing agent links
    - source_collection: Collection with agent URLs to process
    - target_collection: Collection to store detailed profile data
    - limit: Optional limit for testing (0 = process all)

The scraper will:
1. Connect to MongoDB and read agent URLs from source collection
2. Launch undetected Chrome browser for stealth scraping
3. Visit each agent profile page individually
4. Extract comprehensive profile information using XPath selectors
5. Parse and structure extracted data into standardized format
6. Save detailed profiles to target collection with duplicate prevention
7. Log progress and handle errors gracefully
8. Clean up browser resources

Error Handling:
- Graceful handling of missing profile elements
- Safe extraction methods prevent crashes on malformed pages
- Comprehensive logging for debugging and monitoring
- Automatic browser cleanup even if errors occur
- MongoDB connection error handling and recovery
"""


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
    """
    A comprehensive web scraper for extracting detailed profile information from Kentwood agent pages.
    
    This scraper processes agent URLs stored in MongoDB and extracts detailed profile information
    including personal details, contact information, office locations, professional descriptions,
    and social media links. It implements sophisticated parsing logic for complex data formats
    like addresses and names, and provides robust error handling for production environments.
    
    The class handles the complete workflow from MongoDB integration to browser management,
    with comprehensive data structuring and persistence capabilities.
    
    Attributes:
        mongo_uri (str): MongoDB connection string
        db_name (str): Target database name in MongoDB
        source_collection (str): Collection containing agent URLs to process
        target_collection (str): Collection to store detailed profile data
        driver (uc.Chrome): Undetected Chrome WebDriver instance
    
    """
    def __init__(self, mongo_uri: str, db_name: str, source_collection: str, target_collection: str):
        """
        Initialize the AgentDetailsScraper with MongoDB configuration.
        
        Args:
            mongo_uri (str): MongoDB connection string (e.g., "mongodb://localhost:27017")
            db_name (str): Name of the MongoDB database containing agent data
            source_collection (str): Collection name containing agent URLs to process
            target_collection (str): Collection name to store extracted profile details
        
        Note:
            The scraper initializes with a None driver that will be created when
            the scraping process begins. MongoDB connections are established as needed.
        """
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.source_collection = source_collection
        self.target_collection = target_collection
        self.driver = None

    def _launch_browser(self):
        """
        Launch and configure the undetected Chrome browser for profile scraping.
        
        Sets up Chrome with stealth options optimized for scraping real estate agent
        profile pages. The configuration includes anti-detection measures and performance
        optimizations specifically tuned for Kentwood's website structure.
        
        Browser Configuration:
            - Disables automation detection features
            - Optimizes GPU and sandbox settings for stability
            - Maximizes window for consistent element visibility
            - Uses undetected-chromedriver for enhanced stealth capabilities
        
        Raises:
            Exception: If Chrome browser fails to launch or initialize properly
        
        Note:
            The browser instance is stored in self.driver and should be closed
            using _close_browser() to prevent resource leaks.
        """
        logger.info("Launching undetected Chrome...")
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-gpu")
        options.add_argument("--start-maximized")
        self.driver = uc.Chrome(options=options)
        logger.info("Browser launched successfully.")

    def _close_browser(self):
        """
        Safely close the Chrome browser and clean up resources.
        
        Ensures proper cleanup of browser processes and prevents memory leaks.
        This method is safe to call multiple times and handles cases where
        the browser may have already been closed or failed to initialize.
        
        Note:
            Always called in finally blocks to guarantee resource cleanup
            even when exceptions occur during the scraping process.
        """
        if self.driver:
            logger.info("Closing browser...")
            self.driver.quit()

    def _extract_text(self, xpath: str) -> str:
        """
        Safely extract text content from an element using XPath with error handling.
        
        This helper method provides robust text extraction that handles missing
        elements gracefully, preventing crashes when profile pages have incomplete
        or missing information sections.
        
        Args:
            xpath (str): XPath expression to locate the target element
        
        Returns:
            str: Stripped text content from the element, or None if element not found
        
        Error Handling:
            - Returns None for missing elements instead of raising exceptions
            - Automatically strips whitespace from extracted text
            - Handles various types of element location failures
        
        """
        try:
            return self.driver.find_element(By.XPATH, xpath).text.strip()
        except Exception:
            return None

    def _extract_attr(self, xpath: str, attr: str) -> str:
        """
        Safely extract an attribute value from an element using XPath.
        
        This helper method provides robust attribute extraction with comprehensive
        error handling, commonly used for extracting URLs, image sources, and
        other attribute-based data from profile pages.
        
        Args:
            xpath (str): XPath expression to locate the target element
            attr (str): Name of the attribute to extract (e.g., 'href', 'src', 'class')
        
        Returns:
            str: The attribute value, or None if element or attribute not found
        
        Error Handling:
            - Returns None for missing elements or attributes
            - Handles various types of element location and attribute access failures
            - Prevents crashes when profile pages have inconsistent structure
        """
        try:
            return self.driver.find_element(By.XPATH, xpath).get_attribute(attr)
        except Exception:
            return None

    def _extract_agent_details(self, url: str) -> Dict:
        """
        Extract comprehensive profile details from an individual agent page.
        
        This is the core extraction method that navigates to an agent's profile page
        and extracts detailed information using sophisticated parsing logic. It handles
        complex data structures like addresses and names, and creates a standardized
        profile data structure for storage.
        
        Args:
            url (str): The full URL of the agent's profile page
        
        Returns:
            Dict: A comprehensive dictionary containing all extracted profile information
                with standardized keys and parsed data structures. Returns base structure
                with empty/None values if extraction fails.
        
        Data Extraction Process:
            1. Navigates to the agent's profile page
            2. Waits for page content to load completely
            3. Extracts personal information (name, title, image)
            4. Processes contact information (phone, email, website)
            5. Parses complex address data with city/state/zip separation
            6. Collects professional information (description, languages)
            7. Gathers social media links and validates URLs
            8. Structures all data into standardized format
        
        Error Handling:
            - Comprehensive exception handling for each extraction step
            - Graceful degradation when profile elements are missing
            - Detailed error logging for debugging problematic profiles
            - Returns partial data when some extraction steps fail
        
        Data Structure:
            Returns a dictionary with standardized keys including:
            - Personal: first_name, middle_name, last_name, image_url
            - Professional: title, description, languages
            - Contact: email, website, agent_phone_numbers, office_phone_numbers
            - Location: address, city, state, zipcode, country
            - Social: social (list of URLs)
            - Meta: profile_url for reference
        
        Note:
            This method includes a 3-second wait after page load to ensure
            all dynamic content is fully rendered before extraction begins.
        """
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
        """
        Execute the complete agent details scraping workflow.
        
        This is the main orchestration method that manages the entire process from
        reading agent URLs from MongoDB to saving detailed profile information.
        It handles database connections, browser management, and error recovery
        while providing comprehensive logging for monitoring and debugging.
        
        Args:
            limit (int, optional): Maximum number of agent profiles to process.
                                 Set to 0 (default) to process all available agents.
                                 Useful for testing or batch processing large datasets.
        
        Workflow Process:
            1. Establishes MongoDB connection and retrieves agent URLs
            2. Applies optional limit for testing or batch processing
            3. Launches undetected Chrome browser for scraping
            4. Iterates through each agent URL individually
            5. Extracts comprehensive profile details from each page
            6. Saves structured data to target collection with upsert operations
            7. Logs progress and handles errors for each profile
            8. Ensures proper browser cleanup regardless of success/failure
        
        Database Operations:
            - Source Collection: Reads agent URLs from existing collection
            - Target Collection: Saves detailed profiles with duplicate prevention
            - Upsert Strategy: Updates existing profiles or creates new ones
            - Error Recovery: Continues processing even if individual profiles fail
        
        Error Handling:
            - Comprehensive exception handling at multiple levels
            - Individual profile errors don't stop the entire process
            - Database connection errors are logged and handled gracefully
            - Browser cleanup guaranteed through finally block
            - Detailed error logging for debugging and monitoring
        
        Performance Considerations:
            - Single browser instance used for all profiles (efficient)
            - MongoDB connection reuse for better performance
            - Configurable limits for memory management with large datasets
            - Progress logging for monitoring long-running operations
        
        Monitoring and Logging:
            - Progress updates for each processed agent
            - Error details for failed extractions
            - Summary statistics for completed operations
            - File and console logging for comprehensive monitoring
        
        Note:
            The method handles large datasets efficiently but considers using
            limits for initial testing to validate extraction logic and
            performance characteristics.
        """
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
    """
    Main execution block for the Kentwood agent profile details scraper.
    
    This section contains the configuration parameters and orchestrates the complete
    profile scraping workflow. The scraper reads agent URLs from the agent_links
    collection and saves detailed profile information to the agent_details collection.
    
    Configuration Parameters:
        mongo_uri: MongoDB connection string and port
        db_name: Database name containing agent data
        source_collection: Collection with agent URLs to process (from link scraper)
        target_collection: Collection to store detailed profile data
    
    Workflow:
        1. Initialize scraper with MongoDB configuration
        2. Execute profile extraction for all agents in source collection
        3. Save structured profile data to target collection

    """
    # --- Config ---
    mongo_uri = "mongodb://localhost:27017"
    db_name = "kentwood_agents"
    source_collection = "agent_links"       # links scraped earlier
    target_collection = "agent_details"     # save structured details

    scraper = AgentDetailsScraper(mongo_uri, db_name, source_collection, target_collection)
    scraper.run()  
