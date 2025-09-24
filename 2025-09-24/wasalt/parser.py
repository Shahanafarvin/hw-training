#!/usr/bin/env python3
import requests
from lxml import html
from pymongo import MongoClient
import logging
import time


class WasaltPropertyScraper:
    def __init__(
        self,
        mongo_uri="mongodb://localhost:27017/",
        db_name="wasalt",
        source_collection="properties",
        target_collection="property_details",
    ):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.source_collection = self.db[source_collection]
        self.target_collection = self.db[target_collection]

    def fetch_page(self, url):
        """Fetch property detail page"""
        logging.info(f"Fetching property: {url}")
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.text
    
    def parse_property_details(self, html_content, url):
        """Extract property details (key-value pairs)"""
        tree = html.fromstring(html_content)

        details = {}

        # Loop through each <li> inside the details list
        for li in tree.xpath("//ul[contains(@class,'style_propInfodetails__')]/li"):
            key = li.xpath(".//div[contains(@class,'style_propInfodetailcaption__')]/text()")
            value_number = li.xpath(".//div[contains(@class,'style_propInfodetailfigure__')]/span[1]/text()")
            value_unit = li.xpath(".//div[contains(@class,'style_propInfodetailfigure__')]/span[2]/text()")

            if key:
                clean_key = key[0].strip()
                clean_value = ""
                if value_number:
                    clean_value += value_number[0].strip()
                if value_unit:
                    clean_value += " " + value_unit[0].strip()

                details[clean_key] = clean_value.strip()
        #print(details)
        return details

    def parse_additional_info(self, html_content):
        """Extract 'Additional Information' section as key-value pairs"""
        tree = html.fromstring(html_content)
        additional_info = {}

        for div in tree.xpath("//div[contains(@class,'style_infoSectionInnerContainer__')]"):
            key = div.xpath(".//span[contains(@class,'style_infoLable__')]/text()")
            value = div.xpath(".//span[contains(@class,'style_name__')]/text()")

            if key and value:
                clean_key = key[0].strip()
                clean_value = value[0].strip()
                additional_info[clean_key] = clean_value

        return additional_info


    def parse_property(self, html_content, url):
        """Extract property details with XPath"""
        tree = html.fromstring(html_content)

    
        # These XPaths may need refinement after checking real page structure
        title = tree.xpath("//div[@class='stylenewPDP_TitleApartmentHeading__wjLoX stylenewPDP_pdpTitle__W0MJI']/text()")
        price = tree.xpath("//div[contains(@class,'style_price__XdLHZ')]//text()")
        location = tree.xpath("//div[contains(@class,'stylenewPDP_propInfoAdd__RK56b')]//text()")
        breadcrumbs=tree.xpath('//div[@class="stylenewPDP_breadcrumbsWrapper__0MHQi"]//li//text()')
        
        paragraphs = tree.xpath('//div[@class="style_pdpDescWrapper__k9Zzv   style_pdpDescWrapperNew__eXJE2"]//p/text()')
        description = " ".join([p.strip() for p in paragraphs if p.strip()])
        #print(description)
        data = {
            "url": url,
            "title": title[0].strip() if title else "",
            "price": price[0].strip() if price else "",
            "location": " ".join(l.strip() for l in location) if location else "",
            "bedrooms": self.parse_property_details(html_content, url).get("bedrooms", ""),
            "land_area": self.parse_property_details(html_content, url).get("land area", ""),
            "breadcrumbs": " > ".join(breadcrumbs).strip() if breadcrumbs else "",
            "additional_info": self.parse_additional_info(html_content),
            "description": description,
            "scraped_at": time.strftime("%Y-%m-%d"),
        }
        return data

    def save_to_mongo(self, data):
        """Insert into target collection (avoiding duplicates by URL)"""
        if not self.target_collection.find_one({"url": data["url"]}):
            self.target_collection.insert_one(data)
            logging.info(f"Saved details for: {data['url']}")
        else:
            logging.info(f"Already exists in details: {data['url']}")

    def run(self, limit=None):
        """Loop through property URLs and extract details"""
        urls_cursor = self.source_collection.find()
        if limit:
            urls_cursor = urls_cursor.limit(limit)

        for entry in urls_cursor:
            url = entry["url"]
            try:
                html_content = self.fetch_page(url)
                details = self.parse_property(html_content, url)
                self.save_to_mongo(details)
                time.sleep(1)  # polite delay
            except Exception as e:
                logging.error(f"Error processing {url}: {e}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    scraper = WasaltPropertyScraper()
    scraper.run()
