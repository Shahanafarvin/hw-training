import scrapy
from urllib.parse import urljoin


class NextSpider(scrapy.Spider):
    name = "next"
    allowed_domains = ["next.co.uk"]
    start_urls = ["https://www.next.co.uk/women"]

    base_url = "https://www.next.co.uk"

    ids = [
        "multi-11-teaser-474850-3_item_",
        "multi-11-teaser-479476-3_item_",
        "multi-11-teaser-474318-3_item_",
        "multi-11-teaser-473758-3_item_",
        "multi-11-teaser-478208-3_item_",
        "multi-3-teaser-1013880-2_item_",
        "multi-11-teaser-475374-3_item_",
        "multi-11-teaser-657180-3_item_",
        "multi-11-teaser-480676-3_item_",
        "multi-11-teaser-472530-3_item_",
        "multi-11-teaser-473438-3_item_",
        "multi-3-teaser-286336-3_item_",
    ]

    def parse(self, response):
        category_links = response.xpath('//li[contains(@class,"header-16hexny")]/a/@href').getall()

        for link in category_links:
            category_url = urljoin(self.base_url, link)
            yield scrapy.Request(
                url=category_url,
                callback=self.parse_category,
                meta={"category_url": category_url},
            )

    def parse_category(self, response):
        category_url = response.meta["category_url"]
        for id_value in self.ids:
            xpath_query=f"//div[contains(@id, '{id_value}')]/div/a/@href"
            sub_links = response.xpath(xpath_query).getall()

            for sub_link in sub_links:
                full_sub_link = urljoin(self.base_url, sub_link)
                yield scrapy.Request(
                    url=full_sub_link,
                    callback=self.parse_subcategory,
                    meta={"category_url": category_url, "sub_url": full_sub_link},
                )

    def parse_subcategory(self, response):
        category_url = response.meta["category_url"]
        sub_url = response.meta["sub_url"]

        product_links = response.xpath('//a[@class="MuiCardMedia-root  produc-1mup83m"]/@href').getall()
        product_link = []
        for link in product_links:
            full_link = urljoin(self.base_url, link)
            product_link.append(full_link)
        yield {
            category_url:{sub_url:product_links}
        }
