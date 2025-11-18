from mongoengine import Document, StringField, IntField, ListField
from settings import MONGO_COLL_DATA,MONGO_COLL_URLS

class PeoductURLItem(Document):
    meta = {"collection": MONGO_COLL_URLS}
    url = StringField(required=True)

class ProductDataItem(Document):
    meta = {"collection": MONGO_COLL_DATA}
    make = StringField()
    model = StringField()
    year = IntField()
    price = StringField()
    color = StringField()
    VIN = StringField()
    description = StringField()
    image_URLs = ListField(StringField())
    source_link = StringField()
