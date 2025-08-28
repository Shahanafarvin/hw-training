import requests
from bs4 import BeautifulSoup

class Carbon38Parser:
    def __init__(self, product_url):
        self.product_url = product_url
        self.session = requests.Session()
        self.parsed_data = []

    def start(self):
        html = self.fetch_html(self.product_url)
        if html:
            soup = self.parse_data(html)
            product = self.parse_item(soup)
            self.parsed_data.append(product)
        self.save_to_file()
        self.close()

    def fetch_html(self, url):
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                return response.text
        except:
            pass
        return None

    def parse_data(self, html):
        return BeautifulSoup(html, 'html.parser')

    def parse_item(self, soup):
        title_tag = soup.find('h1', class_='ProductMeta__Title Heading u-h3')
        price_tag = soup.find('span', class_='ProductMeta__Price Price')
        return {
            'title': title_tag.text.strip() if title_tag else 'N/A',
            'price': price_tag.text.strip() if price_tag else 'N/A'
        }

    def save_to_file(self):
        with open("carbon38_product.txt", "w", encoding="utf-8") as f:
            for product in self.parsed_data:
                f.write(f"{product['title']} - {product['price']}\n")

    def close(self):
        self.session.close()


if __name__ == "__main__":
    product_url = "https://carbon38.com/en-in/products/double-layered-melt-tank-black-white?_pos=1&_fid=5fce5bb93&_ss=c"
    parser = Carbon38Parser(product_url)
    parser.start()
