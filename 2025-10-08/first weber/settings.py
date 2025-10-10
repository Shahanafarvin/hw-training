import logging
from pymongo import MongoClient


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Base details
BASE_URL = "https://www.firstweber.com"
API_URL = BASE_URL + "/CMS/CmsRoster/RosterSearchResults"

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "firstweber"
URLS_COLLECTION = "agent_url"
DATA_COLLECTION = "agent_profiles"

# Pagination
PAGE_SIZE = 10

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "referer": "https://www.firstweber.com/roster/Agents",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "cookie": "subsiteID=333277; subsiteDirectory=; culture=en; ASP.NET_SessionId=ovq2e5tskmx5sqq0g5dfoocp; currencyAbbr=USD; currencyCulture=en-US; rnSessionID=734277756116199566; cf_clearance=YOUR_CF_CLEARANCE_HERE"
}

MAX_URLS = 903

# MongoDB Connection
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
urls_collection = db[URLS_COLLECTION]
data_collection = db[DATA_COLLECTION]


# File Export Settings
file_name = "firstweber_agents.csv"
FILE_HEADERS = [
    "agent_url",
    "agent_name",
    "office_name",
    "address",
    "city",
    "state",
    "zipcode",
    "phone_number",
    "email",
    "languages_spoken",
    "specialties",
    "profile_image_url"
]