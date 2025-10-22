# items.py
from mongoengine import Document, StringField, FloatField, IntField, ListField, DictField, connect
from settings import MONGO_DB, MONGO_COLLECTION_URL

# Establish Mongo connection
connect(db=MONGO_DB, host="mongodb://localhost:27017/")

class PropertyUrl(Document):
    """Stores property URLs crawled from Baity"""
    meta = {"collection": MONGO_COLLECTION_URL}
    id = IntField(required=True, unique=True)
    url = StringField(required=True)
    title = StringField()
    price = FloatField()
    agency_name = StringField()
    agency_contact_number = StringField()
    governorate = StringField()
    area = StringField()
    images = ListField()
    property_size = FloatField()
    rate_per_sqft = FloatField()
    property_type = StringField()
    rooms = IntField()
    bathrooms = IntField()
    roads = StringField()
    parking = StringField()
    built_up_area = FloatField()
    classification = StringField()

