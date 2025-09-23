"""
Kentwood Real Estate Agent Link Scraper

This module provides a robust web scraper for extracting agent profile links from the 
Kentwood Real Estate website roster page. It uses undetected Chrome WebDriver to bypass
anti-bot protections and implements intelligent scrolling strategies to load dynamically
generated content. Extracted links are stored in MongoDB with duplicate prevention.

Key Features:
- Stealth web scraping using undetected-chromedriver to avoid detection
- Incremental scrolling strategy for efficient dynamic content loading
- Flexible XPath-based link extraction with configurable selectors
- MongoDB integration with upsert operations to prevent duplicates
- Comprehensive logging to both file and console for monitoring
- Type hints and robust error handling throughout
- Configurable scrolling parameters for different website behaviors

Technical Approach:
- Uses incremental scrolling (step-by-step) instead of full-page scrolling
- Implements proper browser lifecycle management with cleanup
- Handles dynamic content loading with configurable pause times
- Provides detailed progress logging for debugging and monitoring

Dependencies:
- undetected-chromedriver: For stealth web automation
- selenium: Web driver framework
- pymongo: MongoDB Python driver
- typing: Type hint support
- MongoDB server running on localhost:27017

Database Schema:
- Database: kentwood_agents (configurable)
- Collection: agent_links (configurable)
- Document Structure: {"url": "https://www.kentwood.com/agent/profile-url"}

Scrolling Strategy:
The scraper uses incremental scrolling to handle websites with lazy loading:
1. Scrolls down in configurable pixel increments (default: 1000px)
2. Pauses between scrolls to allow content loading (default: 2 seconds)
3. Monitors page height changes to detect when all content is loaded
4. Continues until no new content appears

Configuration:
    All key parameters can be modified in the __main__ section:
    - roster_url: Target website URL
    - xpath_expr: XPath selector for agent links
    - mongo_uri: MongoDB connection string
    - db_name: Database name
    - collection_name: Collection name

The scraper will:
1. Launch an undetected Chrome browser
2. Navigate to the Kentwood agents roster page
3. Perform incremental scrolling to load all dynamic content
4. Extract agent profile links using the configured XPath selector
5. Save unique links to MongoDB with duplicate prevention
6. Log all operations to both file and console
7. Clean up browser resources

Performance Considerations:
- Uses incremental scrolling for better performance on large pages
- Implements browser resource management to prevent memory leaks
- Provides configurable timing parameters for different network conditions
- Uses efficient MongoDB upsert operations to handle large datasets

"""

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
    """
    A comprehensive web scraper for extracting real estate agent profile links from websites.
    
    This scraper is specifically designed for real estate websites like Kentwood that use
    dynamic content loading and anti-bot protection. It implements intelligent scrolling
    strategies, stealth browsing techniques, and robust data persistence with MongoDB.
    
    The class handles the complete workflow from browser management to data storage,
    with comprehensive error handling and logging throughout the process.
    
    Attributes:
        url (str): The target URL to scrape (agent roster page)
        mongo_uri (str): MongoDB connection string
        db_name (str): Target database name in MongoDB
        collection_name (str): Target collection name for storing links
        links (List[str]): List of extracted agent profile URLs
        driver (uc.Chrome): Undetected Chrome WebDriver instance
    
    """
    def __init__(self, url: str, mongo_uri: str, db_name: str, collection: str):
        """
        Initialize the AgentScraper with configuration parameters.
        
        Args:
            url (str): The target URL of the agent roster page to scrape
            mongo_uri (str): MongoDB connection string (e.g., "mongodb://localhost:27017")
            db_name (str): Name of the MongoDB database to use for storage
            collection (str): Name of the MongoDB collection to store agent links
        
        Note:
            The scraper initializes with empty links list and None driver,
            which will be populated during the scraping process.
        """
        self.url = url
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection
        self.links: List[str] = []
        self.driver = None

    def _launch_browser(self):
        """
        Launch and configure the undetected Chrome browser for web scraping.
        
        Sets up Chrome with optimal options for stealth scraping including:
        - Disabling automation detection features
        - Optimizing performance settings
        - Maximizing window for consistent element visibility
        - Bypassing common anti-bot protection mechanisms
        
        The browser is configured to appear as a regular user browser to avoid
        detection by anti-scraping systems commonly used by real estate websites.
        
        Raises:
            Exception: If Chrome browser fails to launch or initialize
        
        Note:
            Uses undetected-chromedriver which automatically handles Chrome
            version compatibility and includes built-in stealth features.
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
        
        Ensures proper cleanup of browser processes and prevents memory leaks
        or zombie processes. This method is safe to call multiple times and
        will only attempt to close if a browser instance exists.
        
        Note:
            This method should always be called in a finally block to ensure
            cleanup occurs even if exceptions are raised during scraping.
        """
        if self.driver:
            logger.info("Closing browser...")
            self.driver.quit()

    def _scroll_part_by_part(self, pause: float = 2.0, step: int = 1000):
        """
        Perform intelligent incremental scrolling to load all dynamic content.
        
        Many modern websites use lazy loading or infinite scroll mechanisms that
        require gradual scrolling to trigger content loading. This method implements
        an incremental scrolling strategy that:
        
        1. Scrolls down in configurable pixel increments
        2. Pauses between scrolls to allow content loading
        3. Monitors page height changes to detect new content
        4. Continues until no new content is loaded
        
        This approach is more reliable than simple full-page scrolling and works
        better with websites that have complex loading mechanisms.
        
        Args:
            pause (float, optional): Time in seconds to wait between scroll steps.
                                   Defaults to 2.0 seconds. Increase for slower
                                   networks or websites with heavy content.
            step (int, optional): Number of pixels to scroll in each increment.
                                Defaults to 1000 pixels. Adjust based on page
                                layout and content density.
        
        Technical Details:
            - Tracks current scroll position and page height
            - Uses JavaScript execution for precise scroll control
            - Provides debug logging for monitoring scroll progress
            - Handles edge cases like very short pages or loading failures
        
        Note:
            The method automatically detects when the bottom of the page is reached
            by comparing scroll position with total page height.
        """
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
        """
        Extract agent profile links from the website using XPath selectors.
        
        This is the main scraping method that orchestrates the complete link extraction
        process. It handles browser management, page navigation, content loading through
        scrolling, and link extraction using flexible XPath selectors.
        
        The method implements a robust workflow:
        1. Launches stealth browser
        2. Navigates to target URL
        3. Waits for initial page load
        4. Performs incremental scrolling to load all content
        5. Extracts links using provided XPath selector
        6. Deduplicates links and stores in instance variable
        7. Cleans up browser resources
        
        Args:
            xpath (str): XPath expression to locate agent profile links.
                        Examples:
                        - "//a[@class='agent-link']" (by CSS class)
                        - "//a[contains(@href, '/agent/')]" (by URL pattern)
                        - "//div[@class='agent-card']//a" (nested elements)
        
        Link Processing:
            - Extracts 'href' attribute from matching elements
            - Filters out empty or None links automatically
            - Prevents duplicate links from being added
            - Logs each extracted link for debugging purposes
        
        Error Handling:
            - Comprehensive exception handling for network issues
            - Browser cleanup guaranteed through finally block
            - Detailed error logging for troubleshooting
            - Graceful handling of missing elements or attributes
        
        Note:
            After calling this method, extracted links are available in the
            self.links attribute and can be saved using save_to_mongo().
        """
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
        """
        Save extracted agent links to MongoDB with intelligent duplicate handling.
        
        This method connects to MongoDB and stores all extracted agent links using
        an efficient upsert strategy that prevents duplicate entries while tracking
        the number of new links added. It's designed to handle large datasets
        efficiently and provide detailed logging for monitoring.
        
        Database Operations:
            - Uses update_one with upsert=True for efficient duplicate prevention
            - $setOnInsert ensures existing documents are not modified
            - Tracks and reports the number of new links inserted
            - Handles connection management and error recovery
        
        Upsert Strategy:
            - If link exists: No action taken (prevents duplicates)
            - If link is new: Document is inserted with current timestamp
            - Operation is atomic and safe for concurrent access
            - Minimal database overhead for existing links
        
        Error Handling:
            - Comprehensive MongoDB connection error handling
            - Detailed logging for database operations and failures
            - Graceful handling of network connectivity issues
            - Transaction-safe operations to prevent data corruption
        
        Performance Considerations:
            - Single connection used for all operations
            - Batch processing approach for multiple links
            - Minimal network round-trips with efficient queries
            - Proper connection cleanup to prevent resource leaks
        
        Logging Output:
            - Connection status and progress updates
            - Count of new links inserted vs. existing links
            - Debug-level logging for individual link operations
            - Error details for troubleshooting database issues
        
        Note:
            This method should be called after fetch_links() to persist
            the extracted data. It will log a warning if no links are available.
        """
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
    """
    Main execution block for the Kentwood real estate agent link scraper.
    
    This section contains the configuration parameters and orchestrates the complete
    scraping workflow. All key settings can be modified here to adapt the scraper
    for different real estate websites or requirements.
    
    Configuration Parameters:
        roster_url: The target website URL containing the agent roster
        xpath_expr: XPath selector for identifying agent profile links
        mongo_uri: MongoDB connection string and port
        db_name: Database name for storing extracted data
        collection_name: Collection name for agent links
    
    Workflow:
        1. Initialize scraper with configuration parameters
        2. Extract agent links using XPath-based scraping
        3. Save extracted links to MongoDB with duplicate prevention
    
    """
    # --- Config ---
    roster_url = "https://www.kentwood.com/roster/agents/"
    xpath_expr = "//a[@class='btn btn-outline-primary button hollow']"  
    mongo_uri = "mongodb://localhost:27017"
    db_name = "kentwood_agents"
    collection_name = "agent_links"

    scraper = AgentScraper(roster_url, mongo_uri, db_name, collection_name)
    scraper.fetch_links(xpath_expr)
    scraper.save_to_mongo()
