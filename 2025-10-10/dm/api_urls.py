import requests
import json
from urllib.parse import urljoin

# Base URL for DM Austria content API
BASE_URL = "https://content.services.dmtech.com/rootpage-dm-shop-de-at"

# Headers to mimic browser
HEADERS = {
    "accept": "application/json",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "origin": "https://www.dm.at",
    "pragma": "no-cache",
    "referer": "https://www.dm.at/",
    "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
}


# Recursive extraction of visible categories
def extract_categories(categories, parent_path=""):
    results = []
    for cat in categories:
        if not cat.get("hidden", False):
            name = cat.get("title", "Unknown")
            link = cat.get("link", None)
            full_path = f"{parent_path} > {name}" if parent_path else name
            results.append({"path": full_path, "link": link})
            if "children" in cat and isinstance(cat["children"], list):
                results.extend(extract_categories(cat["children"], full_path))
    return results

# Fetch main navigation
root_url = f"{BASE_URL}?view=navigation&mrclx=false"
response = requests.get(root_url, headers=HEADERS)
data = response.json()

root_categories = data.get("navigation", {}).get("children", [])

all_categories = extract_categories(root_categories)
print(all_categories)

output_data = []

# Loop each category and extract DMSearchProductGrid data
for cat in all_categories:
    link = cat["link"]
    if not link:
        continue

    cat_url = urljoin(BASE_URL + "/", link.lstrip("/") + "?mrclx=false")
    print(cat_url)

    try:
        resp = requests.get(cat_url, headers=HEADERS)
        if resp.status_code == 200:
            cat_json = resp.json()

            main_data = cat_json.get("mainData", [])
            for item in main_data:
                if item.get("type") == "DMSearchProductGrid":
                    query = item.get("query", {})
                    filters = query.get("filters", "")
                    sort = query.get("sort", "")
                    num_products = query.get("numberOfProducts", {}).get("desktop", 0)

                    output_data.append({
                        "category_path": cat["path"],
                        "category_link": link,
                        "filters": filters,
                        "sort": sort,
                        "product_count_desktop": num_products
                    })
        else:
            print(f"Failed: {cat_url} ({resp.status_code})")

    except Exception as e:
        print(f"Error fetching {link}: {e}")

# Save to JSON
with open("dm_category_filters_sort.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=4)

print(f" Saved details for {len(output_data)} categories.")
