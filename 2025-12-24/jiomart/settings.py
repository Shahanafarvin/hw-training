from datetime import datetime
import time
import calendar
import logging
import pytz

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# basic details
PROJECT = ""
CLIENT_NAME = ""
PROJECT_NAME = "jiomart"
FREQUENCY = ""
BASE_URL = "https://www.dillards.com/"


datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))

iteration = datetime_obj.strftime("%Y_%m_%d")
YEAR = datetime_obj.strftime("%Y")
MONTH = datetime_obj.strftime("%m")
DAY = datetime_obj.strftime("%d")
MONTH_VALUE = calendar.month_abbr[int(MONTH.lstrip("0"))]
WEEK = (int(DAY) - 1) // 7 + 1

FILE_NAME = f"{PROJECT_NAME}_{iteration}.csv"

# Mongo db and collections
MONGO_DB = f"{PROJECT_NAME}_{iteration}"
MONGO_COLLECTION_PRODUCTS= f"{PROJECT_NAME}_products"
MONGO_COLLECTION_URL_FAILED = f"{PROJECT_NAME}_url_failed"
MONGO_COLLECTION_DATA = f"{PROJECT_NAME}_data"

"""Settings file for JioMart crawler"""

headers = {
    'accept': '*/*',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'content-type': 'application/json',
    'origin': 'https://www.jiomart.com',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://www.jiomart.com/c/groceries/biscuits-drinks-packaged-foods/tea-coffee/29009',
    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
}

LOCATIONS = [
    {
        "city": "Mumbai",
        "pincode": "400054",
        "state_code": "MH"
    },
    {
        "city": "Chennai",
        "pincode": "600056",
        "state_code": "TN"
    }
]

def get_cookies(city, pincode, state_code):
    """Generate cookies with location-specific values"""
    return {
        'nms_mgo_state_code': state_code,
        'WZRK_G': '0c50d4f36c2346edaa505fb45de11fc1',
        '_fbp': 'fb.1.1766557996359.244939257',
        '_gcl_au': '1.1.1269692634.1766557997',
        '_ALGOLIA': 'anonymous-354dc5e5-9a2b-4b49-b2e9-e9b4594a8c9a',
        'nms_mgo_city': city,
        '_ga': 'GA1.1.921928667.1766557997',
        '__tr_jr': 'W3sidXRtcyI6Im9yZ2FuaWMiLCJ0cyI6IjIwMjYtMDEtMDVUMDQ6MjA6NDIuODYwWiIsImVuYyI6InllcyJ9XQ==',
        'AKA_A2': 'A',
        'nms_mgo_pincode': pincode,
        '_ga_XHR9Q2M3VV': 'GS2.1.s1767675519$o8$g1$t1767675528$j51$l0$h1983932190',
        'RT': '"z=1&dm=www.jiomart.com&si=89d00df5-6db3-47d9-a410-65212c37c15a&ss=mk24d0r7&sl=2&tt=2t8&obo=1&rl=1"',
        'WZRK_S_88R-W4Z-495Z': '%7B%22p%22%3A3%2C%22s%22%3A1767675516%2C%22t%22%3A1767675541%7D',
        '__tr_luptv': '1767675541770',
    }

def get_json_data():
    """Generate base JSON data for the request"""
    return {
        'pageSize': 50,
        'facetSpecs': [
            {
                'facetKey': {
                    'key': 'brands',
                },
                'limit': 500,
                'excludedFilterKeys': [
                    'brands',
                ],
            },
            {
                'facetKey': {
                    'key': 'categories',
                },
                'limit': 500,
                'excludedFilterKeys': [
                    'categories',
                ],
            },
            {
                'facetKey': {
                    'key': 'attributes.category_level_4',
                },
                'limit': 500,
                'excludedFilterKeys': [
                    'attributes.category_level_4',
                ],
            },
            {
                'facetKey': {
                    'key': 'attributes.category_level_1',
                },
                'excludedFilterKeys': [
                    'attributes.category_level_4',
                ],
            },
            {
                'facetKey': {
                    'key': 'attributes.avg_selling_price',
                    'return_min_max': True,
                    'intervals': [
                        {
                            'minimum': 0.1,
                            'maximum': 100000000,
                        },
                    ],
                },
            },
            {
                'facetKey': {
                    'key': 'attributes.avg_discount_pct',
                    'return_min_max': True,
                    'intervals': [
                        {
                            'minimum': 0,
                            'maximum': 99,
                        },
                    ],
                },
            },
        ],
        'variantRollupKeys': [
            'variantId',
        ],
        'branch': 'projects/sr-project-jiomart-jfront-prod/locations/global/catalogs/default_catalog/branches/0',
        'pageCategories': [
            '29009',
        ],
        'userInfo': {
            'userId': None,
        },
        'orderBy': 'attributes.popularity desc',
        'filter': 'attributes.status:ANY("active") AND attributes.category_ids:ANY("29009") AND (attributes.available_regions:ANY("TXCF", "PANINDIAGROCERIES")) AND (attributes.inv_stores_1p:ANY("ALL", "T7GZ") OR attributes.inv_stores_3p:ANY("ALL", "groceries_zone_non-essential_services", "general_zone", "groceries_zone_essential_services"))',
        'visitorId': 'anonymous-16b88074-4641-4f8e-b5f9-c4e9141e3536',
    }

# parser config
PARSER_HEADERS = {
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}

def get_headers_with_location(location, pincode, statecode, url):
        """Generate headers with location-specific cookies"""
        headers = PARSER_HEADERS.copy()
        
        # Build cookie string with location data
        cookie_parts = [
            f'nms_mgo_state_code={statecode}',
            'WZRK_G=0c50d4f36c2346edaa505fb45de11fc1',
            '_fbp=fb.1.1766557996359.244939257',
            '_gcl_au=1.1.1269692634.1766557997',
            '_gid=GA1.2.292933366.1766560675',
            '_ALGOLIA=anonymous-354dc5e5-9a2b-4b49-b2e9-e9b4594a8c9a',
            f'nms_mgo_pincode={pincode}',
            f'nms_mgo_city={location}',
            '_ga=GA1.1.921928667.1766557997',
            'AKA_A2=A',
            f'__tr_luptv={int(time.time() * 1000)}',
            f'WZRK_S_88R-W4Z-495Z=%7B%22p%22%3A7%2C%22s%22%3A{int(time.time())}%2C%22t%22%3A{int(time.time())}%7D',
            '_ga_XHR9Q2M3VV=GS2.1.s1766557997$o1$g1$t1766563473$j56$l0$h276523973',
            'RT="z=1&dm=www.jiomart.com&si=28169922-12e9-42de-b3c4-81979c1a2143&ss=mjjn0lxt&sl=f&tt=oiu&obo=7&rl=1"'
        ]
        
        headers['cookie'] = '; '.join(cookie_parts)
        headers['pin'] = str(pincode)
        headers['referer'] = url
        
        return headers