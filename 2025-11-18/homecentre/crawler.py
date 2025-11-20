import logging
import json
from mongoengine import connect
from curl_cffi import requests
from items import ProductUrlItem, CategoryUrlItem
from settings import MONGO_DB, ALGOLIA_HEADERS


class Crawler:
    """Crawling Urls"""

    def __init__(self):
        self.mongo = connect(db=MONGO_DB, host="localhost", alias="default")
        self.session = requests.Session()

    def start(self):
        """Requesting Start url"""

        categories = [c.category for c in CategoryUrlItem.objects()]
        logging.info(f"Loaded {len(categories)} categories from DB")

        for category in categories:

            meta = {}
            meta['category'] = category
            page = meta.get("page", 0)  

            api_url = (
                "https://3hwowx4270-dsn.algolia.net/1/indexes/*/queries"
                "?X-Algolia-API-Key=4c4f62629d66d4e9463ddb94b9217afb"
                "&X-Algolia-Application-Id=3HWOWX4270"
                "&X-Algolia-Agent=Algolia%20for%20vanilla%20JavaScript%202.9.7"
            )

            logging.info(f"\nFetching category → {category}")

            while True:

                facet_filters = json.dumps([
                    "inStock:1",
                    "approvalStatus:1",
                    f"allCategories:{category}",
                    "badge.title.en:-LASTCHANCE"
                ])

                params = (
                    f"query=*&hitsPerPage=42&page={page}&facets=*&facetFilters={facet_filters}"
                    "&getRankingInfo=1&clickAnalytics=true"
                    "&attributesToHighlight=null"
                    "&attributesToRetrieve=name,url,price,thumbnailImg,gallaryImages,summary,wasPrice,itemType,productType"
                    "&numericFilters=price>0.9"
                    "&maxValuesPerFacet=500"
                )

                payload = json.dumps({
                    "requests": [
                        {"indexName": "prod_uae_homecentre_Product", "params": params}
                    ]
                })

                response = self.session.post(api_url, headers=ALGOLIA_HEADERS, data=payload)

                if response.status_code == 200:
                    is_next = self.parse_item(response, meta)
                    if not is_next:
                        logging.info("Pagination completed")
                        break

                    # pagination crawling
                    page += 1
                    meta["page"] = page



    def parse_item(self, response, meta):
        """item part"""

        data = response.json()
        results = data["results"][0]
        PRODUCTS = results.get("hits", [])
        NB_PAGES = results.get("nbPages", 0)

        # EXTRACT
        products = PRODUCTS
        if products:
            for product in products:
                name = product.get("name", {}).get("ar", "")
                product_id = product.get("objectID", "")
                details_string = product.get("summary", {}).get("ar", "")
                price = product.get("price", "")
                was_price = product.get("wasPrice", "")
                image = product.get("gallaryImages", [])
                product_type = product.get("productType", "")

                # Extract URL
                url = None
                url_part = product.get("url", "")
                for value in url_part.values():
                    if isinstance(value, dict) and "ar" in value:
                        url_slug = value["ar"]
                        url = "https://www.homecentre.com/ae/ar/" + url_slug
                        break

                if not url:
                    continue

                # Duplicate check
                if ProductUrlItem.objects(url=url).first():
                    logging.info(f"Skipping duplicate → {url}")
                    continue

                # ITEM YEILD
                item = {}
                item['url'] = url
                item['product_id'] = product_id
                item['product_name'] = name
                item['details_string'] = details_string
                item['price'] = price
                item['wasprice'] = was_price
                item['image'] = image
                item['product_type'] = product_type
                item['category'] = meta.get('category')
                #logging.info(item)
                try:
                    ProductUrlItem(**item).save()
                except:
                    pass

            page = meta.get("page", 0)
            logging.info(f"Page {page+1}/{NB_PAGES} — {len(products)} items fetched")

            # Check if more pages exist
            if page + 1 >= NB_PAGES:
                return False
            return True

        return False

    def close(self):
        """Close function for all module object closing"""

        self.mongo.close()
        


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()