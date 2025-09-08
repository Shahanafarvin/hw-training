import requests
from lxml import html
from urllib.parse import urljoin
import json

def get_category_links(start_url):
    """Get category links from the main page"""
    response = requests.get(start_url)
    print(response.status_code)
    html_content = html.fromstring(response.content)
    category_links = html_content.xpath('//li[@class=" header-16hexny"]/a/@href')
    return category_links

def get_subcategory_links(category_url, ids):
    """Get subcategory links from a category page"""
    subcategory_links = []
    category_response = requests.get(category_url)
    category_html = html.fromstring(category_response.content)
    
    print(f"\n\nSubcategories for {category_url}:")
    for id_value in ids:
        links = category_html.xpath(f'//div[contains(@id,"{id_value}")]/div/a/@href')
        subcategory_links.extend(links)
    
    return subcategory_links

def get_product_urls(sub_url, base_url):
    """Get product URLs from a single subcategory page (no pagination)"""
    product_urls = set()
    print(f"Fetching products from: {sub_url}")
    res = requests.get(sub_url)
    tree = html.fromstring(res.content)
    
    # Product URLs (look for /style/ links)
    links = tree.xpath('//a[@class="MuiCardMedia-root  produc-1mup83m"]/@href')
    for link in links:
        full_link = urljoin(base_url, link)
        product_urls.add(full_link)
    
    return list(product_urls)

def scrape_next_products():
    """Main function to scrape Next.co.uk products"""
    base_url = "https://www.next.co.uk"
    start_url = "https://www.next.co.uk/women"
    
    # List of IDs to iterate through (subcategory containers)
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
        "multi-3-teaser-286336-3_item_"
    ]
    
    # Get category links
    category_links = get_category_links(start_url)
    
    # Final results dictionary
    all_data = {}
    
    for link in category_links[1:]:
        category_url = urljoin(base_url, link)
        
        # Initialize category in results if not exists
        if category_url not in all_data:
            all_data[category_url] = {}
        
        # Get subcategory links for this category
        subcategory_links = get_subcategory_links(category_url, ids)
        
        for sub_link in subcategory_links:
            full_sub_link = urljoin(base_url, sub_link)
            print(f" Subcategory: {full_sub_link}")
            
            # Get product URLs from this subcategory
            product_urls = get_product_urls(full_sub_link, base_url)
            all_data[category_url][full_sub_link] = product_urls
            print(f"  Found {len(product_urls)} products")
    
    return all_data

def save_to_json(data, filename="next_products.json"):
    """Save data to JSON file"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"\nData saved to {filename}")

if __name__ == "__main__":
    # Run the scraper
    product_data = scrape_next_products()
    save_to_json(product_data)