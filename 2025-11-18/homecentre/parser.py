import logging
import time
from mongoengine import connect
from curl_cffi import requests
from parsel import Selector
from items import ProductUrlItem, ProductItem, ProductFailedItem
from settings import HOMEPAGE_HEADERS, MONGO_DB


class Crawler:
    """Crawling Urls"""

    def __init__(self):
        self.mongo = connect(db=MONGO_DB, host="localhost", alias="default")
        self.session = requests.Session()

    def start(self):
        """Requesting Start url"""

        products = ProductUrlItem.objects()
        total = products.count()
        logging.info(f"Parser started – total urls: {total}")

        for product in products:

            url = product.url or ""
            if not url:
                continue

            meta = {}
            meta['product'] = product

            logging.info(f"Parsing → {url}")

            response = self.session.get(url, headers=HOMEPAGE_HEADERS, impersonate="chrome", timeout=60)

            if response.status_code == 200:
                self.parse_item(response, meta)
            else:
                logging.warning(f"Non-200 status for {url}: {response.status_code}")
                
                ProductFailedItem(url=url).save()
                logging.info(f"Saved failed URL: {url}")

            time.sleep(0.5)

    def parse_item(self, response, meta):
        """item part"""

        sel = Selector(response.text)
        product = meta.get('product')

        # XPATH
        ATTRIBUTE_GROUPS_XPATH = "//div[contains(@class,'attribute-group-v2')]"
        GROUP_TITLE_XPATH = ".//p[contains(@class,'attribute-group-title')]/text()"
        HORIZONTAL_ATTR_XPATH = ".//div[contains(@class,'attribute-group-desc-horizontal1')]//div[contains(@class,'attribute-v2')]"
        ATTR_NAME_XPATH = ".//p[contains(@class,'attribute-v2-name')]/text()"
        ATTR_VALUE_XPATH = ".//p[contains(@class,'attribute-v2-value')]/text()"
        TABLE_ROW_XPATH = ".//div[contains(@class,'attribute-group-desc-table')]//div[contains(@class,'row')]"
        TABLE_KEY_XPATH = ".//div[contains(@class,'attribute-table-key')]/text()"
        TABLE_VALUE_XPATH = ".//div[contains(@class,'attribute-table-value')]/text()"
        COLOR_XPATH = "//li[@id='filter-form-colo-item-0']/input/@data-product-color"
        BREADCRUMB_XPATH = "//ol[@id='breadcrumb']/li//text()"
        STOCK_XPATH = "//strong[@id='product-stock']//text()"

        # EXTRACT
        groups = sel.xpath(ATTRIBUTE_GROUPS_XPATH)
        if groups:
            # Product specs grouped
            product_specs = {}
            for group in groups:
                heading = group.xpath(GROUP_TITLE_XPATH).get()
                heading = heading.strip() if heading else None

                kv_pairs = {}
                # horizontal attrs
                for attr in group.xpath(HORIZONTAL_ATTR_XPATH):
                    k = attr.xpath(ATTR_NAME_XPATH).get()
                    v = attr.xpath(ATTR_VALUE_XPATH).get()
                    if k and v:
                        kv_pairs[k.strip()] = v.strip()
                # table attrs
                for row in group.xpath(TABLE_ROW_XPATH):
                    k = row.xpath(TABLE_KEY_XPATH).get()
                    v = row.xpath(TABLE_VALUE_XPATH).get()
                    if k and v:
                        kv_pairs[k.strip()] = v.strip()

                if heading and kv_pairs:
                    product_specs[heading] = kv_pairs

            quantity = product_specs.get("الوزن والأبعاد")
            material = product_specs.get("الخامة")
            specifications = product_specs.get("المواصفات العامة")

            color = sel.xpath(COLOR_XPATH).get()
            color = color.strip() if color else ""

            breadcrumbs = " > ".join(sel.xpath(BREADCRUMB_XPATH).getall())

            stock = sel.xpath(STOCK_XPATH).get()
            stock = stock.strip() if stock else ""

            product_type = specifications.get("النوع") if specifications else ""

            # ITEM YEILD
            item = {}
            item['url'] = product.url
            item['product_id'] = product.product_id
            item['product_name'] = product.product_name
            item['product_color'] = color
            item['material'] = material
            item['quantity'] = quantity
            item['details_string'] = product.details_string
            item['specification'] = specifications
            item['price'] = product.price
            item['wasprice'] = product.wasprice
            item['product_type'] = product_type
            item['breadcrumb'] = breadcrumbs
            item['stock'] = stock
            item['image'] = product.image

            #logging.info(item)
            try:
                ProductItem(**item).save()
            except:
                pass

            return True

        return False

    def close(self):
        """Close function for all module object closing"""

        self.mongo.close()


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()