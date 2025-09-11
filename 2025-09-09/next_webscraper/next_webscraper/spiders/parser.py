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

    def clean_field(self, value, replace_map=None):
        if not value:
            return ""
        value = str(value).strip()
        if replace_map:
            for old, new in replace_map.items():
                value = value.replace(old, new)
        return value

    def parse_product_page(self, response):
        html_content = response

        def parse_product_code():
            return self.clean_field(
                html_content.xpath('normalize-space(//span[@data-testid="product-code"]/text())').get()
            )
        
        def parse_title():
            return self.clean_field(
                html_content.xpath('normalize-space(//h1[@data-testid="product-title"]/text())').get()
            )
        
        def parse_price():
            return self.clean_field(
                html_content.xpath('normalize-space(//div[@data-testid="product-now-price"]/span/text())').get(),
                replace_map={"£": ""}
            )
        
        def parse_description():
            return self.clean_field(
                html_content.xpath('normalize-space(//p[@data-testid="item-description"]/text())').get()
            )
        
        def parse_colors():
            return self.clean_field(
                html_content.xpath('normalize-space(//span[@data-testid="selected-colour-label"]/text())').get()
            )
        
        def parse_images():
            image_urls = html_content.xpath('//img[@data-testid="image-carousel-slide"]/@src').getall()
            return [url for url in image_urls if url and url.startswith("http")]
        
        def parse_rating():
            return self.clean_field(
                html_content.xpath('normalize-space(//figure[@class="MuiBox-root pdp-css-1uitb0y"]/@aria-label)').get(),
                replace_map={"Stars": ""}
            )
        
        def parse_reviews_count():
            reviews = html_content.xpath('//span[@data-testid="rating-style-badge"]/text()').getall()
            return self.clean_field(reviews[1]) if len(reviews) > 1 else ""
        
        def parse_breadcrumb():
            crumbs = html_content.xpath('//span[@class="MuiChip-label MuiChip-labelMedium pdp-css-11lqbxm"]/text()').getall()
            return [self.clean_field(c) for c in crumbs if self.clean_field(c)]

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
            'colors': parse_colors(),
            'images': parse_images(),
            'rating': parse_rating(),
            'reviews_count': parse_reviews_count(),
            'category_breadcrumb': parse_breadcrumb()
        }

        yield product_data