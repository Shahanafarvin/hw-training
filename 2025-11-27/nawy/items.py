from mongoengine import DynamicDocument, StringField, BooleanField, DictField, ListField, IntField, FloatField
from settings import (
    MONGO_COLLECTION_URLS,
    MONGO_COLLECTION_DATA,
    MONGO_COLLECTION_URL_FAILED
)


class ProductUrlItem(DynamicDocument):
    """initializing URL fields and its Data-Types"""

    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_URLS}
    id = StringField()
    reference_number = StringField()
    url = StringField(required=True)
    broker_display_name = StringField()
    broker= StringField()
    currency = StringField()
    price = FloatField()
    title = StringField()
    bathrooms = IntField()
    bedrooms = IntField()
    property_type = StringField()
    
class ProductDataItem(DynamicDocument):
    """initializing Data fields and its Data-Types"""

    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_DATA}
    id = StringField()
    reference_number = StringField()
    url = StringField(required=True)
    broker_display_name = StringField()
    broker= StringField()
    currency = StringField()
    price = FloatField()
    title = StringField()
    bathrooms = IntField()
    bedrooms = IntField()
    property_type = StringField()
    location = StringField()
    description = StringField()
    amenities = ListField(StringField())
    number_of_photos = IntField()
    details = DictField()
    scraped_ts = StringField()
    date=StringField()
    phone_number=StringField()