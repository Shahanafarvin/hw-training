from datetime import datetime
import calendar
import logging
import pytz


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# basic details
PROJECT = "matalanme"
CLIENT_NAME = "matalanme"
PROJECT_NAME = "matalanme"
FREQUENCY = "N/A"
BASE_URL = "https://www.matalanme.com"

datetime_obj = datetime.now(pytz.timezone("Asia/Kolkata"))
iteration = datetime_obj.strftime("%Y_%m_%d")
YEAR = datetime_obj.strftime("%Y")
MONTH = datetime_obj.strftime("%m")
DAY = datetime_obj.strftime("%d")
MONTH_VALUE = calendar.month_abbr[int(MONTH.lstrip("0"))]
WEEK = (int(DAY) - 1) // 7 + 1

FILE_NAME = f"{PROJECT_NAME}_{iteration}.csv"

# Mongo db and collections
MONGO_DB = f"{PROJECT_NAME}_2025_11_20"
MONGO_COLLECTION_CATEGORY = f"{PROJECT_NAME}_category_uids"
MONGO_COLLECTION_URL_FAILED = f"{PROJECT_NAME}_url_failed"
MONGO_COLLECTION_PLP = f"{PROJECT_NAME}_products"
MONGO_COLLECTION_PDP = f"{PROJECT_NAME}_products_detailed"


HEADERS = {
    'accept': '*/*',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'content-type': 'application/json',
    'origin': 'https://www.matalanme.com',
    'pragma': 'no-cache',
    'referer': 'https://www.matalanme.com/',
    'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'cross-site',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
    'website': 'matalan',
    'store': 'matalan_ae_en',
}

# crawler config
API_URL = "https://api.bfab.com/graphql?product_version=1533"

QUERY = """
query GetProductList($filter: ProductAttributeFilterInput, $pageSize: Int, $currentPage: Int, $sort: ProductAttributeSortInput) {
  products(
    filter: $filter
    pageSize: $pageSize
    currentPage: $currentPage
    sort: $sort
  ) {
    total_count
    aggregations {
      count
      attribute_code
      label
      __typename
      options {
        count
        label
        value
        swatch_data {
          value
          __typename
        }
        __typename
      }
    }
    page_info {
      current_page
      page_size
      total_pages
      __typename
    }
    items {
      id
      sku
      name
      url_key
      brand_name
      home_delivery
      store_pickup
      color_label {
        color_label
        background_color_label
        __typename
      }
      product_label
      stock_status
      is_new
      is_bestseller
      is_featured
      __typename
      hover_image
      rating_aggregation_value
      image {
        label
        __typename
      }
      thumbnail {
        url
        label
        __typename
      }
      categories {
        id
        name
        __typename
      }
      price_range {
        minimum_price {
          regular_price {
            value
            currency
            __typename
          }
          final_price {
            value
            currency
            __typename
          }
          discount {
            amount_off
            percent_off
            __typename
          }
          __typename
        }
        maximum_price {
          regular_price {
            value
            currency
            __typename
          }
          final_price {
            value
            currency
            __typename
          }
          discount {
            amount_off
            percent_off
            __typename
          }
          __typename
        }
        __typename
      }
    }
    __typename
  }
}
"""

# parser config
PARSER_API_URL = "https://api.bfab.com/graphql"

PARSER_HEADERS = {
    'accept': '*/*',
    'content-type': 'application/json',
    'origin': 'https://www.matalanme.com',
    'referer': 'https://www.matalanme.com/',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
    'store': 'matalan_ae_en'
}

PARSER_QUERY = """
query GetProductVarientOptions($url_key: String!) {
  products(filter: {url_key: {eq: $url_key}}) {
    items {
      selected_variant_options(url_key: $url_key) {
        attribute_id
        value_index
        label
        code
        __typename
      }
      __typename
    }
    __typename
  }
}
"""

# export config
FILE_HEADERS = [
    "Url", "Product Name", "Size", "Color", "Quantity", "Brand", "Product Information",
    "currency", "Price", "Product ID", "Price Before Discount", "Gender", "Picture",
    "specifications", "breadcrumbs", "material", "labeling", "availability",
    "category name", "product type"
]