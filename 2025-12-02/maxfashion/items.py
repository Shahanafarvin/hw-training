from mongoengine import DynamicDocument, StringField, DictField, ListField

from settings import MONGO_COLLECTION_CATEGORY, MONGO_COLLECTION_PRODUCTS

class ProductCategoryItem(DynamicDocument):
    """initializing Category fields and its Data-Types"""
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_CATEGORY}
    name = StringField(required=True)
    url = StringField(required=True, unique=True)
    subcategories = ListField(DictField())

class ProductUrlItem(DynamicDocument):
    """initializing URL fields and its Data-Types"""
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_PRODUCTS}
    url = StringField(required=True, unique=True)