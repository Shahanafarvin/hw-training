import requests
from urllib.parse import urljoin
from mongoengine import connect, errors
from settings import CATEGORY_HEADERS, MONGO_DB, logging
from items import ProductCategoryUrlItem


# ==========================
# MongoEngine Connection
# ==========================
MONGO_URI = "mongodb://localhost:27017/"
connect(
    db=MONGO_DB,
    host=MONGO_URI,
    alias="default"
)

# ==========================
# Base URL
# ==========================
BASE_URL = "https://content.services.dmtech.com/rootpage-dm-shop-de-at"

# ==========================
# Fetch Root Navigation
# ==========================
root_url = f"{BASE_URL}?view=navigation&mrclx=false"
response = requests.get(root_url, headers=CATEGORY_HEADERS)

if response.status_code != 200:
    logging.error(f"Failed to fetch root navigation: {response.status_code}")
    exit()

data = response.json()
root_categories = data.get("navigation", {}).get("children", [])
all_categories = []

# ==========================
# Extract Visible Categories
# ==========================
stack = [(root_categories, "")]
while stack:
    categories, parent_path = stack.pop()
    for cat in categories:
        if not cat.get("hidden", False):
            name = cat.get("title", "Unknown")
            link = cat.get("link")
            full_path = f"{parent_path} > {name}" if parent_path else name
            all_categories.append({"path": full_path, "link": link})
            if "children" in cat and isinstance(cat["children"], list):
                stack.append((cat["children"], full_path))

logging.info(f"Total Categories Found: {len(all_categories)}")

# ==========================
# Extract Filters & Sort Info
# ==========================
inserted_count = 0
skipped_count = 0

for cat in all_categories:
    link = cat["link"]
    if not link:
        continue

    cat_url = urljoin(BASE_URL + "/", link.lstrip("/") + "?mrclx=false")
    logging.info(f"Fetching: {cat_url}")

    try:
        resp = requests.get(cat_url, headers=CATEGORY_HEADERS)
        if resp.status_code == 200:
            cat_json = resp.json()
            main_data = cat_json.get("mainData", [])

            for item in main_data:
                if item.get("type") == "DMSearchProductGrid":
                    query = item.get("query", {})
                    filters = query.get("filters", {})
                    sort = query.get("sort", {})
                    num_products = query.get("numberOfProducts", {}).get("desktop", 0)

                    # Create MongoEngine document
                    category_doc = ProductCategoryUrlItem(
                        category_path=cat["path"],
                        category_link=link,
                        filters=filters if filters else "",
                        sort=sort if sort else "",
                        product_count_desktop=num_products if num_products else 0
                    )

                    try:
                        category_doc.save()
                        inserted_count += 1
                    except errors.NotUniqueError:
                        skipped_count += 1
                        continue

        else:
            logging.warning(f"Failed: {cat_url} ({resp.status_code})")

    except Exception as e:
        logging.error(f"Error fetching {link}: {e}")

logging.info(
    f"Inserted {inserted_count} new records, skipped {skipped_count} duplicates "
    f"into collection '{ProductCategoryUrlItem._get_collection_name()}'."
)
