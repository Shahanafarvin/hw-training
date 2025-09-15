import scrapy


class ProductUrlSpider(scrapy.Spider):
    
    name = 'product_urls'
    allowed_domains = ['carbon38.com']
    start_urls = ['https://www.carbon38.com/shop-all-activewear/tops']

    def parse(self, response):
        try:
            product_links = response.xpath('//a[contains(@class,"ProductItem__ImageWrapper ProductItem__ImageWrapper--withAlternateImage")]/@href').getall()

            if not product_links:
                self.logger.warning("No product links found on page: %s", response.url)

            for link in product_links:
                full_url = response.urljoin(link)
                yield {"product_url": full_url}

            next_page = response.xpath('//a[@class="Pagination__NavItem Link Link--primary" and @title="Next page"]/@href').get()
            if next_page:
                yield response.follow(next_page, callback=self.parse)
            else:
                self.logger.info("All pages crawled. No further pagination found.")

        except Exception as e:
            self.logger.error(f"Error parsing {response.url}: {e}", exc_info=True)
            
