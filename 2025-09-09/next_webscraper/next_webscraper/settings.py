

BOT_NAME = "next_webscraper"

SPIDER_MODULES = ["next_webscraper.spiders"]
NEWSPIDER_MODULE = "next_webscraper.spiders"

ADDONS = {}



ROBOTSTXT_OBEY = False
CONCURRENT_REQUESTS = 8
DOWNLOAD_DELAY = 1

CONCURRENT_REQUESTS_PER_DOMAIN = 1

TWISTED_REACTOR = "twisted.internet.selectreactor.SelectReactor"
LOG_LEVEL = "INFO"

