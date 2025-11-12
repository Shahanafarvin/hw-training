from mongoengine import DynamicDocument, StringField, IntField
from settings import MONGO_COLLECTION_URLS, MONGO_COLLECTION_DATA


class ProductItem(DynamicDocument):
    """Stores extracted car details"""
    meta = {"collection": MONGO_COLLECTION_DATA}
    source_link = StringField(unique=True)
    make = StringField()
    model = StringField()
    year = IntField()
    vin = StringField()
    price = IntField()
    mileage = IntField()
    transmission = StringField()
    engine = StringField()
    color = StringField()
    body_style = StringField()
    description = StringField()
    image_url = StringField()


class ProductUrlItem(DynamicDocument):
    """Stores all product URLs"""
    meta = {"collection": MONGO_COLLECTION_URLS}
    url = StringField(required=True)

