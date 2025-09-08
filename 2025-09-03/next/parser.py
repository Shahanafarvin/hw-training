import requests
from lxml import html
import json
import time
import csv
from urllib.parse import urlparse
import re

def parse_product_code(html_content):
    code = html_content.xpath('normalize-space(//span[@data-testid="product-code"]/text())').strip()
    return code if code else "N/A"
    
def parse_title(html_content):
    tittle=html_content.xpath('normalize-space(//h1[@data-testid="product-title"]/text())').strip()
    return tittle if tittle else "N/A"

def parse_price(html_content):
    price=html_content.xpath('normalize-space(//div[@data-testid="product-now-price"]/span/text())').replace("£","").strip()
    return price if price else "N/A"

def parse_description(html_content):
    description=html_content.xpath('normalize-space(//p[@data-testid="item-description"]/text())').strip()
    return description if description else "N/A"

def parse_sizes(tree):
    sizes = tree.xpath('//button[@class="round pdp-css-1drodo6"]/text()')
    return [size.strip() for size in sizes if size.strip()] if sizes else []

def parse_colors(html_content):
    color=html_content.xpath('normalize-space(//span[@data-testid="selected-colour-label"]/text())').strip()
    return color if color else "N/A"

def parse_images(tree):
    image_urls = tree.xpath('//img[@data-testid="image-carousel-slide"]/@src')
    return [url for url in image_urls if url.startswith('http')] if image_urls else []

def parse_rating(html_content):
    rating=html_content.xpath('normalize-space(//figure[@class="MuiBox-root pdp-css-1uitb0y"]/@aria-label)').replace("Stars","").strip()
    return rating if rating else "N/A"

def parse_reviews_count(html_content):
    reviews=html_content.xpath('//span[@data-testid="rating-style-badge"]/text()')
    return reviews[1].strip() if reviews else "N/A"

def parse_breadcrumb(tree):
    breadcrumb = tree.xpath('//span[@class="MuiChip-label MuiChip-labelMedium pdp-css-11lqbxm"]/text()')
    return [crumb.strip() for crumb in breadcrumb if crumb.strip()] if breadcrumb else []

def parse_product_page(product_url):
    try:
        print(f"Parsing: {product_url}")
        response = requests.get(product_url, timeout=30)
        
        if response.status_code != 200:
            print(f"Failed to fetch {product_url} - Status: {response.status_code}")
            return None
            
        html_content = html.fromstring(response.content)
        
        product_data = {
            'url': product_url,
            'title': parse_title(html_content),
            'price': parse_price(html_content),
            'currency': '£',
            'brand': 'Next', 
            'product_code': parse_product_code(html_content),
            'description': parse_description(html_content),
            'sizes': parse_sizes(html_content),
            'colors': parse_colors(html_content),
            'images': parse_images(html_content),
            'rating': parse_rating(html_content),
            'reviews_count': parse_reviews_count(html_content),
            'category_breadcrumb': parse_breadcrumb(html_content)
        }
        
        return product_data
        
    except Exception as e:
        print(f"Error parsing {product_url}: {str(e)}")
        return None


def append_product_to_json(product_data, json_filename):
    try:
        with open(json_filename, 'r', encoding='utf-8') as jsonfile:
            existing_data = json.load(jsonfile)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []
    
    existing_data.append(product_data)
    
    with open(json_filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(existing_data, jsonfile, indent=4, ensure_ascii=False)

def parse_all_products(json_file_path, delay=1, json_filename="next_products_data.json"):
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"File {json_file_path} not found!")
        return 0

    
    total_products = 0
    successful_products = 0
    
    for main_category, subcategories in data.items():
        for subcategory, product_urls in subcategories.items():
            total_products += len(product_urls)
    
    print(f"Total products to parse: {total_products}")
    
    processed = 0
    for main_category, subcategories in data.items():
        print(f"\nProcessing main category: {main_category}")
        
        for subcategory, product_urls in subcategories.items():
            print(f"  Processing subcategory: {subcategory}")
            print(f"  Products in this subcategory: {len(product_urls)}")
            
            for product_url in product_urls:
                processed += 1
                print(f"  Progress: {processed}/{total_products}")
                
                product_data = parse_product_page(product_url)
                if product_data:
                    product_data['main_category'] = main_category
                    product_data['subcategory'] = subcategory
                    
                    try:
                        append_product_to_json(product_data, json_filename)
                        successful_products += 1
                        print(f"Saved product data")
                    except Exception as e:
                        print(f"Failed to save product data: {str(e)}")
                else:
                    print(f"Failed to parse product data")
                
                time.sleep(delay)
    
    print(f"\nParsing completed! Successfully saved {successful_products}/{total_products} products")
    return successful_products

if __name__ == "__main__":
    json_file = "next_products.json"
    
    print("Starting product parsing with immediate saving...")
    successful_count = parse_all_products(
        json_file, 
        delay=1,
        json_filename="next_products_data.json"
    )
    
    print(f"Parsing completed! {successful_count} products saved successfully.")