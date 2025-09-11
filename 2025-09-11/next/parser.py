"""
Next.co.uk Product Detail Parser

A specialized parser for extracting detailed product information from Next.co.uk product pages.
This script reads product URLs from MongoDB (collected by the scraper), visits each product page,
extracts comprehensive product details, and stores the parsed data back to MongoDB.

Key Features:
    - Extracts 13+ product attributes (title, price, sizes, images, etc.)
    - Robust error handling and retry mechanisms
    - Progress tracking and comprehensive logging
    - Configurable processing delays to respect rate limits
    - Data validation and cleaning utilities

Workflow:
    1. Reads product URLs from MongoDB collection
    2. Visits each product page individually
    3. Parses structured product data using XPath selectors
    4. Cleans and validates extracted data
    5. Stores complete product information in target collection

Dependencies:
    - requests: HTTP client for fetching product pages
    - parsel: HTML parsing and XPath extraction
    - pymongo: MongoDB database operations
    - re: Regular expression matching for data cleaning
    - datetime: Timestamp generation
    - time: Rate limiting between requests

"""
import requests
from parsel import Selector
import time
import re
from datetime import datetime
import pymongo
import logging
from requests.exceptions import RequestException, Timeout, HTTPError
from pymongo.errors import PyMongoError


# ---------------- Logging Setup ---------------- #
logging.basicConfig(
    filename="product_parser.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


# ---------------- Helpers ---------------- #
def fetch_selector(url):
    """
    Fetch a product page and return a parsel Selector for data extraction.
    
    Makes an HTTP request to the specified URL with appropriate headers and timeout
    settings. Handles common HTTP errors gracefully and returns None on failure
    to allow the parser to continue processing other products.
    
    Args:
        url (str): The product page URL to fetch
        
    Returns:
        Selector or None: parsel.Selector object for successful requests, None for failures
        
    Raises:
        Logs errors but doesn't raise exceptions to maintain processing stability
        
    """
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        return Selector(text=response.text)
    except (RequestException, Timeout, HTTPError) as e:
        logging.error(f"Failed to fetch {url} -> {e}")
        return None

def clean_value(value, default=""):
    """
    Universal data cleaning function for all extracted values.
    
    Handles common data quality issues found in web scraping:
    - Normalizes whitespace (multiple spaces, tabs, newlines)
    - Strips leading/trailing whitespace
    - Handles None values and empty strings
    - Processes both single values and lists
    - Provides configurable default values
    
    Args:
        value: Raw value from web scraping (str, list, or None)
        default (str): Default value to return for empty/None inputs
        
    Returns:
        str or list: Cleaned value(s) or default if input was empty
        
    """
    # Handle None values and empty strings
    if value is None or (isinstance(value, str) and not value.strip()):
        return default
    # Clean string values - normalize whitespace
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    # Clean list values - process each item and filter out empty ones
    if isinstance(value, list):
        cleaned = [clean_value(v, default) for v in value if v and v.strip()]
        return cleaned if cleaned else [default]
    return value

# ---------------- Parsers ---------------- #
def parse_product_code(sel):
    """
    Extract the unique product code/SKU from the product page.
    
    Args:
        sel (Selector): parsel Selector object for the product page
        
    Returns:
        str: Product code or empty string if not found
    """
    return clean_value(sel.xpath('normalize-space(//span[@data-testid="product-code"]/text())').get())


def parse_title(sel):
    """
    Extract the main product title/name.
    
    Args:
        sel (Selector): parsel Selector object for the product page
        
    Returns:
        str: Product title or empty string if not found
    """
    return clean_value(sel.xpath('normalize-space(//h1[@data-testid="product-title"]/text())').get())


def parse_price(sel):
    """
    Extract the current selling price, removing currency symbols.
    
    Looks for the "now price" which represents the current selling price
    (as opposed to original price if item is on sale).
    
    Args:
        sel (Selector): parsel Selector object for the product page
        
    Returns:
        str: Numeric price value without currency symbol, or empty string
    """
    price = sel.xpath('normalize-space(//div[@data-testid="product-now-price"]/span/text())').get()
    return clean_value(price.replace("£", "").strip() if price else None)


def parse_description(sel):
    """
    Extract the product description text.
    
    Args:
        sel (Selector): parsel Selector object for the product page
        
    Returns:
        str: Product description or empty string if not found
    """
    return clean_value(sel.xpath('normalize-space(//p[@data-testid="item-description"]/text())').get())


def parse_sizes(sel):
    """
    Extract all available sizes for the product.
    
    Looks for size selection buttons which contain the size labels.
    Common sizes include: XS, S, M, L, XL, or numeric sizes for shoes, etc.
    
    Args:
        sel (Selector): parsel Selector object for the product page
        
    Returns:
        list: List of available size strings, or empty list
    """
    sizes = sel.xpath('//button[@class="round pdp-css-1drodo6"]/text()').getall()
    return clean_value(sizes)


def parse_colors(sel):
    """
    Extract the currently selected color/variant name.
    
    Args:
        sel (Selector): parsel Selector object for the product page
        
    Returns:
        str: Color name or empty string if not found
    """
    return clean_value(sel.xpath('normalize-space(//span[@data-testid="selected-colour-label"]/text())').get())


def parse_images(sel):
    """
    Extract all product image URLs from the image carousel.
    
    Filters out invalid URLs and returns only HTTP/HTTPS image links.
    These images typically include multiple angles, detail shots, and lifestyle photos.
    
    Args:
        sel (Selector): parsel Selector object for the product page
        
    Returns:
        list: List of valid image URLs, or empty list
    """
    images = sel.xpath('//img[@data-testid="image-carousel-slide"]/@src').getall()
    valid = [url for url in images if url.startswith("http")] if images else []
    return clean_value(valid)


def parse_rating(sel):
    """
    Extract the product's average customer rating.
    
    Parses the star rating from the aria-label attribute and extracts
    just the numeric rating value.
    
    Args:
        sel (Selector): parsel Selector object for the product page
        
    Returns:
        str: Numeric rating value or empty string if not found
    """
    rating = sel.xpath('normalize-space(//figure[@class="MuiBox-root pdp-css-1uitb0y"]/@aria-label)').get()
    return clean_value(rating.replace("Stars", "").strip() if rating else None)


def parse_reviews_count(sel):
    """
    Extract the total number of customer reviews.
    
    The reviews count typically appears as the second element in the rating badge,
    showing how many customers have reviewed the product.
    
    Args:
        sel (Selector): parsel Selector object for the product page
        
    Returns:
        str: Number of reviews or empty string if not found
    """
    reviews = sel.xpath('//span[@data-testid="rating-style-badge"]/text()').getall()
    return clean_value(reviews[1] if len(reviews) > 1 else None)


def parse_breadcrumb(sel):
    """
    Extract the category breadcrumb navigation path.
    
    Returns the hierarchical category path that shows where this product
    sits within the site's category structure (e.g., Women > Dresses > Maxi).
    
    Args:
        sel (Selector): parsel Selector object for the product page
        
    Returns:
        list: List of breadcrumb category names, or empty list
    """
    crumbs = sel.xpath('//span[@class="MuiChip-label MuiChip-labelMedium pdp-css-11lqbxm"]/text()').getall()
    return clean_value(crumbs)


def parse_washing_instructions(sel):
    """
    Extract care/washing instructions from the page's JSON data.
    
    Next.co.uk stores detailed product information in a __NEXT_DATA__ script tag
    as JSON. This function extracts the washing instructions using regex pattern
    matching on the JSON content.
    
    Args:
        sel (Selector): parsel Selector object for the product page
        
    Returns:
        str: Washing instructions text or empty string if not found
        
    Note:
        This approach is more fragile than XPath selection as it depends on
        the JSON structure remaining consistent. However, it's often the only
        way to access certain data that isn't rendered in the HTML.
    """
    script_content = sel.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
    if not script_content:
        return clean_value(None)

    match = re.search(r'"washingInstructions"\s*:\s*"([^"]+)"', script_content)
    return clean_value(match.group(1) if match else None)


def parse_product_page(product_url):
    """
    Main product parsing function that orchestrates all data extraction.
    
    Fetches a product page and extracts all available product information
    using the individual parsing functions. Creates a structured data object
    with consistent field names and data types.
    
    Args:
        product_url (str): Full URL of the product page to parse
        
    Returns:
        dict or None: Complete product data dictionary, or None if parsing failed
    
    """
    sel = fetch_selector(product_url)
    if not sel:
        return None

    product_data = {
        "url": product_url,
        "title": parse_title(sel),
        "price": parse_price(sel),
        "currency": "£",
        "brand": "Next",
        "product_code": parse_product_code(sel),
        "description": parse_description(sel),
        "sizes": parse_sizes(sel),
        "colors": parse_colors(sel),
        "images": parse_images(sel),
        "rating": parse_rating(sel),
        "reviews_count": parse_reviews_count(sel),
        "category_breadcrumb": parse_breadcrumb(sel),
        "washing_instructions": parse_washing_instructions(sel),
        "scraped_dt": datetime.now().strftime("%Y-%m-%d")
    }
    return product_data


# ---------------- Main Parser ---------------- #
def parse_all_products_from_mongo(
    mongo_uri="mongodb://localhost:27017/",
    db_name="nextdb",
    source_collection="products",  # where crawler stored product URLs
    target_collection="product_details",  # where parsed product data will go
    delay=1
):
    """
    Main orchestration function for parsing all products from MongoDB.
    
    Reads product URLs collected by the scraper, processes each product page
    to extract detailed information, and stores the results in a separate
    MongoDB collection. Includes progress tracking, error handling, and
    configurable rate limiting.
    
    Processing Flow:
        1. Connect to MongoDB and read all product URL documents
        2. Count total products for progress tracking
        3. Iterate through each category and subcategory
        4. Parse each individual product page
        5. Enhance product data with category information
        6. Store completed product data in target collection
        7. Apply rate limiting delay between requests
        8. Log progress and handle errors gracefully
    
    Args:
        mongo_uri (str): MongoDB connection string
        db_name (str): Database name containing the collections
        source_collection (str): Collection name with product URLs from scraper
        target_collection (str): Collection name for storing parsed product data
        delay (int): Seconds to wait between product page requests (rate limiting)
        
    Returns:
        int: Number of products successfully parsed and saved
        
    Error Handling:
        - Individual product parsing failures don't stop the overall process
        - Database connection issues are logged and cause early termination
        - Progress is logged regularly for monitoring long-running processes
    """
    try:
        client = pymongo.MongoClient(mongo_uri)
        db = client[db_name]
        source_col = db[source_collection]
        target_col = db[target_collection]

        docs = list(source_col.find({}))
        total_products = sum(len(sub["product_urls"]) for doc in docs for sub in doc["subcategories"])
        logging.info(f"Total products to parse: {total_products}")

        processed = 0
        saved = 0

        for doc in docs:
            category_url = doc["category_url"]

            for sub in doc["subcategories"]:
                sub_url = sub["subcategory_url"]
                product_urls = sub["product_urls"]

                for product_url in product_urls:
                    processed += 1
                    logging.info(f"Processing {processed}/{total_products}: {product_url}")

                    product_data = parse_product_page(product_url)
                    if product_data:
                        product_data["main_category"] = category_url
                        product_data["subcategory"] = sub_url

                        try:
                            target_col.insert_one(product_data)
                            saved += 1
                            logging.info(f"Saved product {product_url}")
                        except PyMongoError as e:
                            logging.error(f"MongoDB insert failed for {product_url}: {e}")
                    else:
                        logging.warning(f"Failed to parse {product_url}")

                    time.sleep(delay)

        logging.info(f"Parsing completed: {saved}/{total_products} products saved successfully")
        return saved

    except PyMongoError as e:
        logging.critical(f"MongoDB error: {e}", exc_info=True)
        return 0
    except Exception as e:
        logging.critical(f"Unexpected error: {e}", exc_info=True)
        return 0


# ---------------- Runner ---------------- #
if __name__ == "__main__":
    """
    Main execution block for standalone script usage.
    """
    logging.info("Starting product parsing...")
    saved_count = parse_all_products_from_mongo()
    logging.info(f"Finished. {saved_count} products saved successfully.")
