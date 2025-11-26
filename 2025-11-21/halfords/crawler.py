import requests
from parsel import Selector
from mongoengine import connect
from items import ProductCategoryItem, ProductUrlItem
from settings import logging, MONGO_DB, MONGO_HOST, MONGO_PORT, REQUEST_TIMEOUT


class Crawler:
    """Crawling Urls"""
    def __init__(self):
        self.mongo = connect(db=MONGO_DB, host=MONGO_HOST, alias="default", port=MONGO_PORT)
        
    def start(self):
        """Requesting Start url"""
        
        category_doc = ProductCategoryItem.objects.first()
        if category_doc:
                categories=category_doc.categories
        
        if not categories:
            logging.error("No categories found in database")
            return
        
        # Iterate through category tree
        for cat, cat_data in categories.items():
            for sub, sub_data in cat_data.get("subcategories", {}).items():
                for subsub, subsub_data in sub_data.get("sub_subcategories", {}).items():
                    url = subsub_data["url"]
                    
                    meta = {}
                    meta['category'] = cat
                    meta['subcategory'] = sub
                    meta['sub_subcategory'] = subsub
                    meta['url'] = url
                    
                    logging.info(f"Processing: {cat} > {sub} > {subsub}")
                    
                    try:
                        response = requests.get(url,timeout=REQUEST_TIMEOUT)
                        if response.status_code == 200:
                            self.parse_item(response, meta)
                        else:
                            logging.warning(f"Status code {response.status_code} for {url}")
                    except Exception as e:
                        logging.error(f"Error fetching {url}: {str(e)}")
    
    
    def parse_item(self, response, meta):
        """item part"""
        sel = Selector(response.text)
        
        # XPATH
        DEEPER_SUBCAT_XPATH = "//li[@class='border-bottom border-gray-200']/a/@href"
        PRODUCT_XPATH = "//a[@data-action-name='plp.product.click']/@href"
        LOADMORE_XPATH = "//a[@data-cmp-id='loadMore']/@href"
        
        # EXTRACT
        more_subcats = sel.xpath(DEEPER_SUBCAT_XPATH).getall()
        
        full_product_links = []

        # CHECK DEEPER SUB-CATEGORIES
        if more_subcats:
            logging.info(f"Found {len(more_subcats)} deeper categories")
            more_subcats = [
                f"https://www.halfords.com{link}" if link.startswith("/") else link
                for link in more_subcats
            ]
            
            for child_url in more_subcats:
                logging.info(f"Visiting deeper: {child_url}")

                page_url = child_url   # IMPORTANT FIX

                while True:
                    try:
                        child_response = requests.get(page_url,timeout=REQUEST_TIMEOUT)
                        if child_response.status_code == 200:

                            child_sel = Selector(child_response.text)
                            product_links = child_sel.xpath(PRODUCT_XPATH).getall()
                            
                            if product_links:
                                logging.info(f"Found {len(product_links)} products on this page")
                                full_product_links.extend(product_links)
                            else:
                                logging.info("No products found on this page")
                                break

                            # PAGINATION
                            next_page = child_sel.xpath(LOADMORE_XPATH).get()
                            
                            if next_page:
                                page_url = (
                                    next_page if next_page.startswith("http")
                                    else f"https://www.halfords.com{next_page}"
                                )
                                logging.info(f"Load More found → Next page: {page_url}")
                            else:
                                logging.info("Pagination completed")
                                break

                        else:
                            logging.warning(f"Status code {child_response.status_code}")
                            break
                            
                    except Exception as e:
                        logging.error(f"Error: {str(e)}")
                        break

        else:
            # NO DEEPER CATEGORIES → DIRECT PAGINATION
            logging.info("No deeper categories → Using pagination directly")
            
            page_url = meta['url']
            meta['page'] = 0
            
            while True:
                try:
                    response = requests.get(page_url,timeout=REQUEST_TIMEOUT)
                    if response.status_code == 200:
                        sel = Selector(response.text)

                        # Extract product links
                        product_links = sel.xpath(PRODUCT_XPATH).getall()
                        if product_links:
                            logging.info(f"Found {len(product_links)} products on this page")
                            full_product_links.extend(product_links)
                        else:
                            logging.info("No products found on this page")
                            break

                        # Pagination (Load more)
                        next_page = sel.xpath(LOADMORE_XPATH).get()
                        if next_page:
                            page_url = (
                                next_page if next_page.startswith("http")
                                else f"https://www.halfords.com{next_page}"
                            )
                            meta['page'] += 1
                            logging.info(f"Load More found → Page {meta['page']}: {page_url}")
                        else:
                            logging.info("Pagination completed")
                            break

                    else:
                        logging.warning(f"Status code {response.status_code}")
                        break

                except Exception as e:
                    logging.error(f"Error during pagination: {str(e)}")
                    break
        
        
        for url in full_product_links:

            # ITEM YIELD
            item = {}
            item["url"] = url
            
            #logging.info(item)
        
            try:
                ProductUrlItem(**item).save()
                logging.info("Saved to database")
            except Exception as e:
                logging.error(f"Error saving: {str(e)}")
                pass

    def close(self):
        """Close function for all module object closing"""
        self.mongo.close()


if __name__ == "__main__":
    crawler = Crawler()
    crawler.start()
    crawler.close()