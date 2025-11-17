from mongoengine import DynamicDocument, StringField
from settings import MONGO_COLLECTION_URLS, MONGO_COLLECTION_DATA

class ProductUrlItem(DynamicDocument):
    """Store scraped vehicle URLs"""
    meta = {"collection": MONGO_COLLECTION_URLS}
    url = StringField(required=True, unique=True)

class ProductItem(DynamicDocument):
    """Store vehicle details"""
    meta = {"collection": MONGO_COLLECTION_DATA}
    url = StringField()
    make = StringField()
    model = StringField()
    year = StringField()
    title = StringField()
    VIN = StringField()
    price = StringField()
    mileage = StringField()
    transmission = StringField()
    engine = StringField()
    color = StringField()
    fuel_type = StringField()
    body_style = StringField()
    description = StringField()
    image_URL = StringField()
