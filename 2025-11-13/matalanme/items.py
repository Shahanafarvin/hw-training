from mongoengine import DynamicDocument, StringField, ListField, BooleanField, FloatField, IntField, DictField
from settings import  MONGO_COLLECTION_URL_FAILED,MONGO_COLLECTION_CATEGORY, MONGO_COLLECTION_PLP, MONGO_COLLECTION_PDP

class CategoryItem(DynamicDocument):
    meta = {"collection": MONGO_COLLECTION_CATEGORY}
    category_name = StringField()
    sub_category_name = StringField()
    sub_category_url = StringField()
    uids = ListField(StringField())

class ProductItem(DynamicDocument):
    meta = {"collection": MONGO_COLLECTION_PLP}
    product_id = IntField()
    name = StringField()
    url_key = StringField()
    brand_name = StringField()
    stock_status = StringField()
    price = FloatField()
    price_before_discount = FloatField()
    currency=StringField()
    labeling = StringField()
    image_url = StringField()
    category_name= StringField()
    breadcrumbs = StringField()

class ProductDetailItem(DynamicDocument):
    meta = {"collection": MONGO_COLLECTION_PDP}
    product_id = IntField()
    name = StringField()
    product_url = StringField()
    brand_name = StringField()
    stock_status = StringField()
    price = FloatField()
    price_before_discount = FloatField()
    currency = StringField()
    labeling = StringField()
    image_url = StringField()
    category_name= StringField()
    breadcrumbs = StringField()
    specifications = DictField()
    product_information = StringField()
    size=StringField()
    color=StringField()

class ProductFailedItem(DynamicDocument):
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_URL_FAILED}
    url = StringField(required=True)
