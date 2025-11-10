from mongoengine import DynamicDocument, StringField, BooleanField, ListField
from settings import MONGO_COLLECTION_URLS,MONGO_COLLECTION_DATA

class ProductUrlItem(DynamicDocument):
    """Mongo model for product URLs"""
    meta = {'collection': MONGO_COLLECTION_URLS}
    url = StringField(required=True)


class ProductItem(DynamicDocument):
    """Mongo model for product details"""
    meta = {'collection': MONGO_COLLECTION_DATA}
    url = StringField()
    title = StringField()
    manufacturer = StringField()
    price = StringField()
    description = StringField()
    equivalent_part_numbers = StringField()
    availability = BooleanField()
    image_urls = ListField(StringField())
