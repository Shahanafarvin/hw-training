import logging
from settings import (
    DataMiningError,
    BASE_URL,
    URL,
    LINK_CSS,
    TITLE_CSS,
    PRICE_CSS,
    setup_logging,
    save_raw_html,
    save_links_to_file,
    yield_lines_from_file,
)
import requests
from bs4 import BeautifulSoup


# Set up logging configuration
setup_logging()


class Carbon38Parser:
    """
    A web scraper for extracting product data from the Carbon38 website.
    """

    def __init__(self, start_url):
        """
        Initialize the parser with the starting URL and session.
        """
        self.start_url = start_url
        self.session = requests.Session()
        self.parsed_data = []

    def start(self):
        """
        Start the scraping process:
        - Fetch the HTML of the starting page.
        - Parse product links and save them to a file.
        - Fetch and parse product details for each link.
        - Save the cleaned product data to a file.
        """
        logging.info("Starting the data mining process.")
        html = self.fetch_html(self.start_url)
        if html:
            save_raw_html(html)  # Save raw HTML to a file
            product_links = self.parse_data(html)
            save_links_to_file(product_links)  # Save product links to a file

            # Process each product link
            for link in yield_lines_from_file("product_links.txt"):
                product_html = self.fetch_html(link.strip())
                if product_html:
                    try:
                        product = self.parse_item(product_html)
                        self.parsed_data.append(product)
                    except DataMiningError as e:
                        logging.error(f"Error parsing product data: {e}")

        self.save_cleaned_data()  # Save cleaned product data to a file
        self.close()

    def fetch_html(self, url):
        """
        Fetch the HTML content of a given URL.

        Args:
            url (str): The URL to fetch.

        Returns:
            str: The HTML content of the page, or None if an error occurs.
        """
        try:
            logging.info(f"Fetching HTML for URL: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.text
        except requests.exceptions.ConnectionError:
            logging.error(f"Connection error while trying to fetch {url}")
        except requests.exceptions.Timeout:
            logging.error(f"Request timed out for {url}")
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP error occurred: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
        return None

    def parse_data(self, html):
        """
        Parse product links from the HTML content.

        Args:
            html (str): The HTML content of the page.

        Returns:
            list: A list of product links.
        """
        try:
            logging.info("Parsing product links from the HTML.")
            soup = BeautifulSoup(html, 'html.parser')
            links = [
                f"{BASE_URL}{a.get('href')}"
                for a in soup.select(LINK_CSS)
                if a.get('href') and a.get('href').startswith('/')
            ]
            return links
        except Exception as e:
            raise DataMiningError(f"Failed to parse data: {e}")

    def parse_item(self, html):
        """
        Parse product details (title and price) from the HTML content.

        Args:
            html (str): The HTML content of the product page.

        Returns:
            dict: A dictionary containing the product title and price.
        """
        try:
            logging.info("Parsing product details from the HTML.")
            soup = BeautifulSoup(html, 'html.parser')
            title_tag = soup.select_one(TITLE_CSS)
            price_tag = soup.select_one(PRICE_CSS)
            if not title_tag or not price_tag:
                raise DataMiningError("Missing title or price in product HTML")
            return {
                'title': title_tag.text.strip(),
                'price': price_tag.text.strip().replace('Rs.', '')
            }
        except Exception as e:
            raise DataMiningError(f"Failed to parse item: {e}")

    def save_cleaned_data(self):
        """
        Save the cleaned product data to a file.
        """
        logging.info("Saving cleaned data to cleaned_data.txt.")
        with open("cleaned_data.txt", "w", encoding="utf-8") as f:
            for product in self.parsed_data:
                f.write(f"{product['title']} - {product['price']}\n")

    def close(self):
        """
        Close the session to release resources.
        """
        logging.info("Closing the session.")
        self.session.close()


if __name__ == "__main__":
    # Initialize the parser with the starting URL
    parser = Carbon38Parser(URL)
    parser.start()

    # Sample product data for demonstration
    sample_products = [
        {"title": "Product 1", "price": "100"},
        {"title": "Product 2", "price": None},
        {"title": "Product 3", "price": "200"},
        {"title": "Product 4", "price": ""},
        {"title": "Product 5", "price": "300"},
    ]

    # Extract only product names
    product_names = [product["title"] for product in sample_products]
    print(f"Product Names: {product_names}")

    # Filter entries with null prices only
    null_price_products = [product for product in sample_products if not product["price"]]
    print(f"Products with Null Prices: {null_price_products}")