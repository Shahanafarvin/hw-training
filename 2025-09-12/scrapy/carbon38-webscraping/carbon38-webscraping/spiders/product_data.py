import json
import scrapy
import pymongo
import re

class ProductDetailSpider(scrapy.Spider):
    """
    Spider Name: product_data

    Purpose:
        - Scrapes detailed product information and review counts from carbon38.com.
        - Reads product URLs from MongoDB (collection: product_urls).
        - Saves enriched product data back into MongoDB (collection: product_data).
    """

    name = 'product_data'
    allowed_domains = ['carbon38.com']

    def __init__(self, *args, **kwargs):
        super(ProductDetailSpider, self).__init__(*args, **kwargs)
        # MongoDB connection
        self.client = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = self.client["carbon38"]
        self.urls_collection = self.db["product_urls"]
        self.data_collection = self.db["product_data"]

    def start_requests(self):
        """
        Reads product URLs from MongoDB and starts scraping.
        """
        try:
            urls = self.urls_collection.find({}, {"product_url": 1, "_id": 0})
            for entry in urls:
                url = entry.get("product_url")
                if url:
                    self.logger.info(f"Crawling product: {url}")
                    yield scrapy.Request(url=url, callback=self.parse_product)
        except Exception as e:
            self.logger.error(f"Error fetching URLs from MongoDB: {e}", exc_info=True)

    def add_https(self, url):
        """Ensure HTTPS schema for image URLs."""
        return f"https:{url}" if url and url.startswith("//") else url
    

    def parse_faq_data(self, response):
        """
        Extracts FAQ section data such as "Editor's Notes", "Size & Fit", and "Fabric & Care".
        """
        faq_section = response.xpath('//section[@data-section-type="faq"]//div[contains(@class,"Faq__ItemWrapper")]')
        faq_data = {}
        for item in faq_section:
            question = item.xpath('.//button[contains(@class,"Faq__Question")]/text()').get(default='').strip()
            answer_parts = item.xpath('.//div[contains(@class,"Faq__AnswerWrapper")]//p//text()').getall()
            answer = " ".join(text.strip() for text in answer_parts if text.strip())
            faq_data[question] = answer
        return faq_data
    
    def extract_rating_from_script(self, response):
        """
        Extracts Yotpo rating from <script id="viewed_product">.
        Returns rating as a string. Returns '0' if not found.
        """
        script_text = response.xpath('//script[@id="viewed_product"]/text()').get(default="")
        rating_match = re.search(r'MetafieldYotpoRating\s*=\s*"([0-9.]+)"', script_text)
        rating = rating_match.group(1) if rating_match else "0"
        return rating.strip()

    def parse_product(self, response):
        """
        Parses product page content and triggers Yotpo API call for review count.
        """
        try:
            faq_data = self.parse_faq_data(response)
            

            product = {
                "product_url": response.url,
                "primary_image_url": self.add_https(
                    response.xpath('//a[contains(@class,"Product__SlideshowNavImage")]//img/@src').get(default="").strip()
                ),
                "brand": response.xpath(
                    '//div[contains(@class,"ProductMeta")]//h2[contains(@class,"ProductMeta__Vendor")]/text() | '
                    '//div[contains(@class,"ProductMeta")]//h2[contains(@class,"ProductMeta__Vendor")]/a/text()'
                ).get(default="").strip(),
                "product_name": response.xpath('//h1[contains(@class,"ProductMeta__Title")]/text()').get(default="").strip(),
                "price": response.xpath(
                    '//span[contains(@class,"ProductMeta__Price")]/text()'
                ).get(default="").replace('$', '').replace('USD', '').strip(),
                "colour": response.xpath('//span[contains(@class,"ProductForm__SelectedValue")]/text()').get(default="").strip(),
                "sizes": response.xpath('//ul[contains(@class,"SizeSwatchList")]//li//label/text()').getall(),
                "description": faq_data.get("Editor's Notes", ""),
                "size_and_fit": faq_data.get("Size & Fit", ""),
                "fabric&care": faq_data.get("Fabric & Care", ""),
                "image_urls": [
                    self.add_https(url)
                    for url in response.xpath('//a[contains(@class,"Product__SlideshowNavImage")]//img/@src').getall()
                ],
                "rating": self.extract_rating_from_script(response),
            }

            # Call Yotpo API to fetch review count
            yield from self.fetch_review_data(response, product)

        except Exception as e:
            self.logger.error(f"Error parsing product page {response.url}: {e}", exc_info=True)

    def fetch_review_data(self, response, product):
        """
        Extracts product ID and calls Yotpo API to fetch review count.
        """
        product_id = response.xpath('//div[contains(@class,"yotpo-widget-instance")]/@data-yotpo-product-id').get()

        if product_id:
            store_id = "77OFfab03RDNwJXqpx5Bl5qmZJcAjybjX3EnuxBh"
            api_url = (
                f"https://api-cdn.yotpo.com/v3/storefront/store/{store_id}"
                f"/product/{product_id}/reviews?page=1&perPage=1"
            )
            yield scrapy.Request(
                url=api_url,
                callback=self.parse_reviews,
                meta={"item_data": product},
                dont_filter=True
            )
        else:
            self.logger.warning(f"No Yotpo product ID found for: {response.url}")
            product["reviews"] = "0 Reviews"
            self.data_collection.update_one(
                {"product_url": product["product_url"]},
                {"$set": product},
                upsert=True
            )
            yield product

    def parse_reviews(self, response):
        """
        Parses the Yotpo API response to extract total review count and saves product to MongoDB.
        """
        item = response.meta.get("item_data", {})
        try:
            data = json.loads(response.text)
            review_count = data.get("pagination", {}).get("total", 0)
            item["reviews"] = f"{review_count}"
        except Exception as e:
            self.logger.warning(f"Failed to parse Yotpo response: {e}")
            item["reviews"] = ""

        # Save final item to MongoDB
        self.data_collection.update_one(
            {"product_url": item["product_url"]},
            {"$set": item},
            upsert=True
        )
        yield item
