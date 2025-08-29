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

# Set up logging
setup_logging()

class Carbon38Parser:
    def __init__(self, start_url):
        self.start_url = start_url
        self.session = requests.Session()
        self.parsed_data = []

    def start(self):
        logging.info("Starting the data mining process.")
        html = self.fetch_html(self.start_url)
        if html:
            save_raw_html(html)  # Save raw HTML to raw.html
            product_links = self.parse_data(html)
            save_links_to_file(product_links)  # Save links to a text file

            # Read links from the file 
            for link in yield_lines_from_file("product_links.txt"):
                product_html = self.fetch_html(link.strip())
                if product_html:
                    try:
                        product = self.parse_item(product_html)
                        self.parsed_data.append(product)
                    except DataMiningError as e:
                        logging.error(f"Error parsing product data: {e}")

        self.save_cleaned_data() 
        self.close()

    def fetch_html(self, url):
        try:
            logging.info(f"Fetching HTML for URL: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status() 
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
        try:
            logging.info("Parsing product links from the HTML.")
            soup = BeautifulSoup(html, 'html.parser')
            links = []
            for a in soup.select(LINK_CSS):
                href = a.get('href')
                if href and href.startswith('/'):
                    links.append(f"{BASE_URL}{href}")
            return links
        except Exception as e:
            raise DataMiningError(f"Failed to parse data: {e}")

    def parse_item(self, html):
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
        logging.info("Saving cleaned data to cleaned_data.txt.")
        with open("cleaned_data.txt", "w", encoding="utf-8") as f:
            for product in self.parsed_data:
                f.write(f"{product['title']} - {product['price']}\n")

    def close(self):
        logging.info("Closing the session.")
        self.session.close()


if __name__ == "__main__":
    parser = Carbon38Parser(URL)
    parser.start()