from mongoengine import DynamicDocument, StringField, IntField, FloatField, DictField, ListField, DateTimeField, BooleanField
from settings import MONGO_COLLECTION_CATEGORY, MONGO_COLLECTION_URLS, MONGO_COLLECTION_DATA

class ProductCategoryUrlItem(DynamicDocument):
    """Stores category filters, sorting, and product count."""
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_CATEGORY}

    category_path = StringField(required=True)
    category_link = StringField(required=True, unique=True)
    filters = StringField()
    sort = StringField()
    product_count_desktop = IntField()


class ProductUrlItem(DynamicDocument):
    """Stores individual product URLs with optional category info."""
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_URLS}

    url = StringField(required=True, unique=True)
    gtin = IntField()
    category_path = StringField()


class ProductDetailItem(DynamicDocument):
    """Stores parsed product details."""
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_DATA}

    unique_id = IntField(required=True, unique=True)
    competitor_name = StringField(required=True)
    extraction_date = DateTimeField(required=True)
    product_name = StringField(required=True)
    brand = StringField()
    grammage_quantity = StringField()
    grammage_unit = StringField()
    regular_price = FloatField()
    selling_price = FloatField()
    price_was = FloatField()
    promotion_price = FloatField()  
    currency = StringField()
    producthierarchy_level_1 = StringField()
    producthierarchy_level_2 = StringField()
    producthierarchy_level_3 = StringField()
    producthierarchy_level_4 = StringField()
    producthierarchy_level_5 = StringField()
    producthierarchy_level_6 = StringField()
    producthierarchy_level_7 = StringField()
    breadcrumb = StringField()
    pdp_url = StringField()
    variants = StringField()
    file_name_1 = StringField()
    image_url_1 = StringField()
    file_name_2 = StringField() 
    image_url_2 = StringField()
    file_name_3 = StringField()
    image_url_3 = StringField()
    file_name_4 = StringField()
    image_url_4 = StringField()
    file_name_5 = StringField()
    image_url_5 = StringField()
    file_name_6 = StringField()
    image_url_6 = StringField()
    product_description = StringField()
    instructionforuse = StringField()
    instructions = StringField()
    ingredients = StringField()
    manufacturer_address = StringField()
    storage_instructions = StringField()
    preparationinstructions = StringField()
    country_of_origin = StringField()
    allergens = StringField()
    features = StringField()
    organictype = StringField()
    instock = BooleanField()
    upc = IntField()
    product_unique_key = StringField()
