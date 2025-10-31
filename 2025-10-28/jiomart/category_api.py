import requests
from mongoengine import connect
from items import CategoryTreeItem
from settings import MONGO_URI, MONGO_DB, logger, category_api_url as api_url, categoory_headers as headers

# -----------------------
# MongoDB Connection
# -----------------------
connect(MONGO_DB, host=MONGO_URI)

# -----------------------
# Request + JSON parsing
# -----------------------
try:
    response = requests.get(api_url, headers=headers, timeout=30)
    logger.info(f"Requesting: {api_url} → Status {response.status_code}")
    response.raise_for_status()
except requests.RequestException as e:
    logger.error(f" API request failed: {e}")
    exit(1)

data = response.json()
categories = data.get("resultData", [])

if not categories:
    logger.warning(" No categories found in API response")
    exit(0)

# -----------------------
# Parse and Save
# -----------------------

cat_name = categories[0].get("name")
cat_id = categories[0].get("id")
sub_tree = {}

for sub in categories[0].get("sub_categories", []):
    sub_name = sub.get("name")
    sub_id = sub.get("id")
    sub_tree[sub_name] = {"id": sub_id, "sub_categories": {}}

    for sub_sub in sub.get("sub_categories", []):
        sub_sub_name = sub_sub.get("name")
        sub_sub_id = sub_sub.get("id")
        sub_tree[sub_name]["sub_categories"][sub_sub_name] = {"id": sub_sub_id}

try:
    item = CategoryTreeItem(
        category_name=cat_name,
        category_id=cat_id,
        sub_categories=sub_tree
    )
    item.save()
    logger.info(f" Saved category: {cat_name}")
except Exception as e:
    logger.error(f" Error saving category '{cat_name}': {e}")

