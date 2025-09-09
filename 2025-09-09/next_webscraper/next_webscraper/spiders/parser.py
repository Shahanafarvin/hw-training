import scrapy
import json

class NextProductsSpider(scrapy.Spider):
    name = "next_products"
    allowed_domains = ["next.co.uk"]
    
    json_file = "next_products.json"
    
    def start_requests(self):
        try:
            with open(self.json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            self.logger.error(f"File {self.json_file} not found!")
            return

        if not isinstance(data, list):
            self.logger.error("JSON format unexpected. Expected a list of dicts.")
            return

        for entry in data: 
            for main_category, subcategories in entry.items():
                for subcategory, product_urls in subcategories.items():
                    for url in product_urls:
                        self.logger.info(f"Scheduling request → {url}")
                        yield scrapy.Request(
                            url=url,
                            callback=self.parse_product_page,
                            meta={
                                "main_category": main_category,
                                "subcategory": subcategory,
                            },
                        )


    def parse_product_page(self, response):
        html_content = response.xpath
        tree = response

        def parse_product_code():
            return html_content('normalize-space(//span[@data-testid="product-code"]/text())').get(default="N/A").strip()
        
        def parse_title():
            return html_content('normalize-space(//h1[@data-testid="product-title"]/text())').get(default="N/A").strip()
        
        def parse_price():
            return html_content('normalize-space(//div[@data-testid="product-now-price"]/span/text())').get(default="N/A").replace("£", "").strip()
        
        def parse_description():
            return html_content('normalize-space(//p[@data-testid="item-description"]/text())').get(default="N/A").strip()
        
        def parse_sizes():
            sizes = tree.xpath('//button[@class="round pdp-css-1drodo6"]/text()').getall()
            return [s.strip() for s in sizes if s.strip()] if sizes else []
        
        def parse_colors():
            return html_content('normalize-space(//span[@data-testid="selected-colour-label"]/text())').get(default="N/A").strip()
        
        def parse_images():
            image_urls = tree.xpath('//img[@data-testid="image-carousel-slide"]/@src').getall()
            return [url for url in image_urls if url.startswith("http")] if image_urls else []
        
        def parse_rating():
            return html_content('normalize-space(//figure[@class="MuiBox-root pdp-css-1uitb0y"]/@aria-label)').get(default="N/A").replace("Stars", "").strip()
        
        def parse_reviews_count():
            reviews = tree.xpath('//span[@data-testid="rating-style-badge"]/text()').getall()
            return reviews[1].strip() if len(reviews) > 1 else "N/A"
        
        def parse_breadcrumb():
            crumbs = tree.xpath('//span[@class="MuiChip-label MuiChip-labelMedium pdp-css-11lqbxm"]/text()').getall()
            return [c.strip() for c in crumbs if c.strip()] if crumbs else []

        product_data = {
            'url': response.url,
            'main_category': response.meta['main_category'],
            'subcategory': response.meta['subcategory'],
            'title': parse_title(),
            'price': parse_price(),
            'currency': '£',
            'brand': 'Next',
            'product_code': parse_product_code(),
            'description': parse_description(),
            'sizes': parse_sizes(),
            'colors': parse_colors(),
            'images': parse_images(),
            'rating': parse_rating(),
            'reviews_count': parse_reviews_count(),
            'category_breadcrumb': parse_breadcrumb()
        }

        yield product_data
