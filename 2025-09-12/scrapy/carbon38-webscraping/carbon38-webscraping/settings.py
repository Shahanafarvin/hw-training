

BOT_NAME = "carbon38_scraper"

SPIDER_MODULES = ["carbon38_scraper.spiders"]
NEWSPIDER_MODULE = "carbon38_scraper.spiders"

# Add default headers
DEFAULT_REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
}

LOG_LEVEL= 'INFO'  # Set logging level to INFO

# Throttle to prevent system overload
CONCURRENT_REQUESTS = 1
DOWNLOAD_DELAY = 3  # seconds

ITEM_PIPELINES = {
    'carbon38_scraper.pipelines.MongoPipeline': 300,
}

ROBOTSTXT_OBEY = False