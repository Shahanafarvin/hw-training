import requests
from pymongo import MongoClient

BASE_URL = "https://baity.bh/properties/"

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://baity.bh/properties/",
    "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "x-fingerprint": "fce5a48cac25c7fe959605720b5e56af",
    "x-requested-with": "XMLHttpRequest",
}

##############################CRAWLER##############################
API_ENDPOINT = (
    "https://baity.bh/properties/map?"
    "search=&governorateChanged=0&min_latitude=25.82208398833634&"
    "max_latitude=26.346900072646612&min_longitude=50.29025870287133&"
    "max_longitude=50.88489371263695&zoom=11&baity_verified=0&"
    "virtual_tour=0&has_offer=0&filterCount=0&show_recomended=1&page={page}"
)
page = 1
while True:
    api_url = API_ENDPOINT.format(page=page)
    response = requests.get(api_url, headers=HEADERS, timeout=30)
    data = response.json()

    props = data.get("properties", {}).get("data", [])
    last_page = data.get("properties", {}).get("last_page", page)

    for prop in props:
        item = {
            "id": prop.get("id"),
            "url": f"{BASE_URL}{prop.get('slug', '')}" if prop.get("slug") else "",
            "title": prop.get("title") or prop.get("name") or "",
            "price": prop.get("price"),
            "agency_name": prop.get("agency", {}).get("name"),
            "agency_contact_number": prop.get("agency", {}).get("agency_contact_number"),
            "governorate": prop.get("governorate", {}).get("name"),
            "area": prop.get("area", {}).get("name"),
            "images": prop.get("images", []),
            "property_size": prop.get("plot_area"),
            "rate_per_sqft": prop.get("eb_rate"),
            "property_type": prop.get("property_type"),
            "rooms":prop.get("beds"),
            "bathrooms":prop.get("baths"),
            "roads":prop.get("land_road"),
            "parking":prop.get("parking"),
            "built_up_area":prop.get("built_up_area"),
            "classification":prop.get("classification"),
                
        }
        page_count += 1

#########################Findings#############################
#1. No data found in the HTML response; content is loaded dynamically through API calls.
#2. All required data can be extracted directly from the PLP page itself.