import requests
from bs4 import BeautifulSoup

class Carbon38Parser:
    def __init__(self, start_url):
        self.start_url = start_url
        self.session = requests.Session()
        self.parsed_data = []

    def start(self):
        html = self.fetch_html(self.start_url)
        if html:
            self.save_raw_html(html)  
            product_links = self.parse_data(html)
            for link in product_links:
                product_html = self.fetch_html(link) 
                if product_html:
                    product = self.parse_item(product_html)
                    self.parsed_data.append(product)
        self.save_cleaned_data() 
        self.close()

    def fetch_html(self, url):
        try:
            response = self.session.get(url)
            if response.status_code == 200:
                return response.text
        except:
            pass
        return None

    def save_raw_html(self, html):
        with open("raw.html", "w", encoding="utf-8") as f:
            f.write(html)

    def parse_data(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        for a in soup.select('a.ProductItem__ImageWrapper.ProductItem__ImageWrapper--withAlternateImage'):
            href = a.get('href')
            if href and href.startswith('/'):
                links.append('https://carbon38.com' + href)
        return links

    def parse_item(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        title_tag = soup.find('h1', class_='ProductMeta__Title Heading u-h3')
        price_tag = soup.find('span', class_='ProductMeta__Price Price')
        return {
            'title': title_tag.text.strip() if title_tag else 'N/A',
            'price': price_tag.text.strip().replace('Rs.','') if price_tag else 'N/A'
        }

    def save_cleaned_data(self):
        with open("cleaned_data.txt", "w", encoding="utf-8") as f:
            for product in self.parsed_data:
                f.write(f"{product['title']} - {product['price']}\n")

    def close(self):
        self.session.close()


if __name__ == "__main__":
    url = "https://carbon38.com/en-in/collections/tops"
    parser = Carbon38Parser(url)
    parser.start()