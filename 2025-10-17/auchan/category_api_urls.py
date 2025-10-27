import requests
from settings import HEADERS, logging, MONGO_DB, MONGO_URI
from items import ProductCategoryItem, SubCategory
from mongoengine import connect

# Connect to MongoDB
connect(db=MONGO_DB, host=MONGO_URI)


def fetch_subcategories(parent_id):
    """
    Recursively fetch subcategories for a given category
    """
    url = f"https://auchan.hu/api/v2/cache/tree/{parent_id}?depth=1&cacheSegmentationCode=&hl=hu"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch categories for parent_id={parent_id}: {e}")
        return []

    data = response.json()
    subcategories = []

    for cat in data.get("children", []):
        # Only include non-boutique categories
        if cat.get("boutique", True) is False:
            cat_id = cat.get("id")
            cat_name = cat.get("name")
            child_count = cat.get("childCount", 0)

            # Recursively fetch children
            children = fetch_subcategories(cat_id) if child_count != 0 else []

            subcat = SubCategory(
                category_id=cat_id,
                category_name=cat_name,
                child_count=child_count,
                category_api=f"https://auchan.hu/api/v2/cache/tree/{cat_id}?depth=1&cacheSegmentationCode=&hl=hu",
                category_products_api=f"https://auchan.hu/api/v2/cache/products?categoryId={cat_id}&page=1&itemsPerPage=12&filters[]=available&filterValues[]=1&cacheSegmentationCode=&hl=hu",
                subcategories=children
            )
            subcategories.append(subcat)

    return subcategories


def fetch_top_categories():
    """
    Fetch top-level categories and their full subcategory tree
    """
    url = "https://auchan.hu/api/v2/cache/tree/0?depth=1&cacheSegmentationCode=&hl=hu"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        logging.info("Fetched top-level categories")
    except requests.RequestException as e:
        logging.error(f"Failed to fetch top-level categories: {e}")
        return

    data = response.json()
    for cat in data.get("children", []):
        if cat.get("boutique", True) is False:
            cat_id = cat.get("id")
            cat_name = cat.get("name")
            child_count = cat.get("childCount", 0)

            # Recursively get subcategories
            subcategories = fetch_subcategories(cat_id) if child_count != 0 else []

            # Save the full tree as one document
            record = ProductCategoryItem(
                category_id=cat_id,
                category_name=cat_name,
                child_count=child_count,
                category_api=f"https://auchan.hu/api/v2/cache/tree/{cat_id}?depth=1&cacheSegmentationCode=&hl=hu",
                category_products_api=f"https://auchan.hu/api/v2/cache/products?categoryId={cat_id}&page=1&itemsPerPage=12&filters[]=available&filterValues[]=1&cacheSegmentationCode=&hl=hu",
                subcategories=subcategories
            )
            record.save()
            logging.info(f"Saved top-level category {cat_name} with {len(subcategories)} subcategories")


if __name__ == "__main__":
    fetch_top_categories()
