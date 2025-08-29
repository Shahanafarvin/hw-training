# settings.py
import logging

# Constants
BASE_URL = "https://carbon38.com"
URL = f"{BASE_URL}/en-in/collections/tops"
LINK_CSS = "a.ProductItem__ImageWrapper.ProductItem__ImageWrapper--withAlternateImage"
TITLE_CSS = "h1.ProductMeta__Title.Heading.u-h3"
PRICE_CSS = "span.ProductMeta__Price.Price"

# File paths
RAW_HTML_FILE = "raw.html"
CLEANED_DATA_FILE = "cleaned_data.txt"
LOG_FILE = "scraper.log"

# Custom Exception
class DataMiningError(Exception):
    def __init__(self, message):
        super().__init__(message)

# Logging Setup
def setup_logging():
    logging.basicConfig(
        filename="data_mining.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

# Helper Functions
def save_raw_html(html):
    logging.info("Saving raw HTML to raw.html.")
    with open("raw.html", "w", encoding="utf-8") as f:
        f.write(html)

def save_links_to_file(links):
    logging.info("Saving product links to product_links.txt.")
    with open("product_links.txt", "w", encoding="utf-8") as f:
        for link in links:
            f.write(link + "\n")

def yield_lines_from_file(file_path):
    """Generator method to yield lines from a file one by one."""
    logging.info(f"Reading lines from file: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            yield line
