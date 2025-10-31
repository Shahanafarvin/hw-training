from mongoengine import DynamicDocument, StringField, DictField, IntField, ListField, FloatField
from settings import MONGO_COLLECTION_CATEGORY, MONGO_COLLECTION_PRODUCTS, MONGO_COLLECTION_DATA

class CategoryTreeItem(DynamicDocument):
    meta = {'collection': MONGO_COLLECTION_CATEGORY}  # MongoDB collection name

    category_name = StringField(required=True)
    category_id = IntField(required=True)
    sub_categories = DictField()

class ProductItem(DynamicDocument):
    meta = {'collection': MONGO_COLLECTION_PRODUCTS}

    unique_id = StringField(required=True)
    brand = StringField()
    title = StringField()
    pdp_url = StringField()
    images = ListField()
    category_path = ListField()
    alternate_ids = StringField()

class ProductEnrichedItem(DynamicDocument):

    meta = {"collection": MONGO_COLLECTION_DATA}
    product_id = StringField(required=True)
    pdp_url = StringField()
    brand = StringField()
    title = StringField()
    images = ListField()
    category_path = ListField()
    availability = StringField()
    discount = FloatField()
    mrp = FloatField()
    selling_price = FloatField()   
    description = StringField()
    product_info = DictField()
    average_rating = FloatField()
    review_count = FloatField()
    alternate_ids = StringField()