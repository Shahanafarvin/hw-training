import json
from curl_cffi import requests
from mongoengine import connect
from items import ProductUrlItem
from settings import MONGO_DB, HOMEPAGE_HEADERS,ALGOLIA_HEADERS, logging


class Crawler:
    """Crawler for HomeCentre API using Algolia"""

    def __init__(self):
        connect(db=MONGO_DB, host="localhost", alias="default", port=27017)
        self.session = requests.Session()

    # ----------------------------------------------------------
    # Extract category key names from homepage (HTML)
    # ----------------------------------------------------------
    def parse_category(self):
        url = "https://www.homecentre.com/ae"
        logging.info("Fetching homepage for category generation…")

        response = requests.get(url, headers=HOMEPAGE_HEADERS, impersonate="chrome")
        from parsel import Selector
        sel = Selector(response.text)

        categories = []
        items = sel.xpath("(//ul[@class='row list-unstyled'])[1]/li")

        for li in items[:3]:
            category_urls = li.xpath(".//ul/li/a/@href").getall()

            for u in category_urls:
                part = u.rstrip("/").split("/")[-1]
                part = part.split("?")[0]
                if part:
                    categories.append(part)

        logging.info(f"Extracted {len(categories)} category names")

        return categories
    
    # ----------------------------------------------------------
    # Start crawling using Algolia API
    # ----------------------------------------------------------
    def start(self):
        logging.info("Crawler started…")

        categories = self.parse_category()

        logging.info(f"Using {len(categories)} categories")

        API_URL = (
            "https://3hwowx4270-dsn.algolia.net/1/indexes/*/queries"
            "?X-Algolia-API-Key=4c4f62629d66d4e9463ddb94b9217afb"
            "&X-Algolia-Application-Id=3HWOWX4270"
            "&X-Algolia-Agent=Algolia%20for%20vanilla%20JavaScript%202.9.7"
        )

        # STEP 2 — Pagination loop
        for category in categories:
            logging.info(f"\nFetching category → {category}")

            page = 0

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

                response = self.session.post(API_URL, headers=ALGOLIA_HEADERS, data=payload)

                if response.status_code != 200:
                    logging.error(f"Error {response.status_code}: {response.text}")
                    break

                data = response.json()
                results = data["results"][0]
                hits = results.get("hits", [])
                nb_pages = results.get("nbPages", 0)

                # ----- Parse each product -----
                for hit in hits:
                    self.parse_item(hit, category)

                logging.info(f"Page {page+1}/{nb_pages} → {len(hits)} items parsed")

                page += 1
                if page >= nb_pages:
                    break


    # ----------------------------------------------------------
    # Parse individual product item from API "hit"
    # ----------------------------------------------------------
    def parse_item(self, hit, category):
        """Extract and save product URL + metadata"""
        name = hit.get("name", {}).get("ar", "")
        product_id = hit.get("objectID", "")

        url_part = hit.get("url", "")
        for value in url_part.values():
            if isinstance(value, dict) and "ar" in value:
                url_slug=value["ar"]
                url= "https://www.homecentre.com/ae/ar/" + url_slug

        # ---------------------------
        # DUPLICATE CHECK
        # ---------------------------
        if ProductUrlItem.objects(url=url).first():
            logging.info(f"Skipping duplicate URL → {url}")
            return
        
        details_string = hit.get("summary", {}).get("ar", "")
        price = hit.get("price", "")
        was_price = hit.get("wasPrice", "")
        image = hit.get("gallaryImages", [])
        product_type=hit.get("productType","")

        # Save to DB
        ProductUrlItem(
            url=url,
            product_id=product_id,
            product_name=name,
            details_string=details_string,
            price=price,
            wasprice=was_price,
            image=image,
            product_type=product_type,
            category=category,
        ).save()

if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
