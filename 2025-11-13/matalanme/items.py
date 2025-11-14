from mongoengine import Document, StringField, ListField, BooleanField, FloatField, IntField, DictField
from settings import MONGO_CATEGORY_COLLECTION, MONGO_PLP_COLLECTION, MONGO_PDP_COLLECTION

class CategoryItem(Document):
    meta = {"collection": MONGO_CATEGORY_COLLECTION}
    category_name = StringField()
    sub_category_name = StringField()
    sub_category_url = StringField()
    uids = ListField(StringField())

class ProductItem(Document):
    meta = {"collection": MONGO_PLP_COLLECTION}
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

class ProductDetailItem(Document):
    meta = {"collection": MONGO_PDP_COLLECTION}
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
