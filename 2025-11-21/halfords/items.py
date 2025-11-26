from mongoengine import DynamicDocument, StringField, DictField

from settings import MONGO_COLLECTION_CATEGORY,MONGO_COLLECTION_PRODUCTS, MONGO_COLLECTION_DATA

class ProductCategoryItem(DynamicDocument):
    """initializing Category fields and its Data-Types"""
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_CATEGORY}
    categories = DictField()

class ProductUrlItem(DynamicDocument):
    """initializing URL fields and its Data-Types"""
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_PRODUCTS}
    url = StringField(required=True,unique=True)

class ProductDataItem(DynamicDocument):
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_DATA}
    url = StringField(unique=True)
    product_name = StringField()
    sku = StringField()
    mpn = StringField()
    breadcrumbs = StringField()
    rating = StringField()
    reviews = StringField()
    currency = StringField()
    selling_price = StringField()
    regular_price = StringField()
    price_label = StringField()
    priceValidUntil = StringField()
    availability = StringField()
    seller = StringField()
    image = StringField()
    features = StringField()
    description = StringField()
    specification = DictField()