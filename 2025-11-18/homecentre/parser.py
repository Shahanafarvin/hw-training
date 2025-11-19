import re
import time
import logging
from curl_cffi import requests
from parsel import Selector
from mongoengine import connect
from items import ProductUrlItem, ProductItem
from settings import MONGO_DB, HOMEPAGE_HEADERS

class Parser:
    def __init__(self):
        connect(db=MONGO_DB, host="localhost", alias="default")
        self.session = requests.Session()

    def start(self, limit=None):
        """
        Iterate over ProductUrlItem entries and parse them.
        """
        qs = ProductUrlItem.objects()
        total = qs.count()
        logging.info(f"Parser started – total urls: {total}")
        counter = 0
        for entry in qs:
            if limit and counter >= limit:
                break
            url = entry.url or ""
            self.parse_item(url,entry)
            time.sleep(0.3)
            counter += 1

    def parse_item(self, url,entry):
        """
        Parse a single product URL and return a ProductItem document (not saved),
        or None on failure.
        """
        logging.info(f"Parsing → {url}")
        try:
            resp = self.session.get(url, headers=HOMEPAGE_HEADERS, impersonate="chrome")
            if resp.status_code not in (200, 404):  # homepage peculiarity earlier; still attempt
                logging.warning(f"Non-200 status for {url}: {resp.status_code}")
            sel = Selector(resp.text)

            # Product specs grouped
            product_specs = {}
            groups = sel.xpath("//div[contains(@class,'attribute-group-v2')]")
            for group in groups:
                heading = group.xpath(".//p[contains(@class,'attribute-group-title')]/text()").get()
                heading = heading.strip() if heading else None

                kv_pairs = {}
                # horizontal attrs
                for attr in group.xpath(".//div[contains(@class,'attribute-group-desc-horizontal1')]//div[contains(@class,'attribute-v2')]"):
                    k = attr.xpath(".//p[contains(@class,'attribute-v2-name')]/text()").get()
                    v = attr.xpath(".//p[contains(@class,'attribute-v2-value')]/text()").get()
                    if k and v:
                        kv_pairs[k.strip()] = v.strip()
                # table attrs
                for row in group.xpath(".//div[contains(@class,'attribute-group-desc-table')]//div[contains(@class,'row')]"):
                    k = row.xpath(".//div[contains(@class,'attribute-table-key')]/text()").get()
                    v = row.xpath(".//div[contains(@class,'attribute-table-value')]/text()").get()
                    if k and v:
                        kv_pairs[k.strip()] = v.strip()

                if heading and kv_pairs:
                    product_specs[heading] = kv_pairs

           
            quantity=product_specs.get("الوزن والأبعاد")
            material=product_specs.get("الخامة")
            specifications=product_specs.get("المواصفات العامة")
            color=sel.xpath("//strong[@id='product-title-01']//text()").get().strip()
            breadcrumbs=" > ".join(sel.xpath("//ol[@id='breadcrumb']/li//text()").getall())
            stock=sel.xpath("//strong[@id='product-stock']//text()").get().strip()

            # Build product item and save
            product = ProductItem(
                url =entry.url,
                product_id =entry.product_id,
                product_name =entry.product_name, 
                product_color= color,
                material= material,
                quantity=quantity,
                details_string=entry.details_string,
                specification=specifications,
                price=entry.price,
                wasprice = entry.wasprice,
                product_type=entry.product_type,
                breadcrumb = breadcrumbs,
                stock = stock,
                image =entry.image,
   
            )
            product.save()
            logging.info(f"Saved product: {url}")
            return product

        except Exception:
            logging.exception(f"Failed to parse {url}")
            return None

if __name__ == "__main__":
    parser = Parser()
    parser.start()
