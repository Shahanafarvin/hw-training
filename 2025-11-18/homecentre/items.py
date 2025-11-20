from mongoengine import DynamicDocument, StringField, IntField, ListField, DictField
from settings import MONGO_COLLECTION_CATEGORY, MONGO_COLLECTION_PRODUCTS, MONGO_COLLECTION_DATA, MONGO_COLLECTION_URL_FAILED

class CategoryUrlItem(DynamicDocument):
    meta = {"collection": MONGO_COLLECTION_CATEGORY}
    category = StringField(unique=True)

class ProductUrlItem(DynamicDocument):
    meta = {"collection": MONGO_COLLECTION_PRODUCTS}
    url = StringField(required=True, unique=True)
    category = StringField()      
    product_id = StringField() 
    product_name=StringField()
    details_string=StringField()
    price=IntField()
    wasprice=IntField()
    image=ListField()
    product_type=StringField()

class ProductItem(DynamicDocument):
    meta = {"collection":MONGO_COLLECTION_DATA}
    url = StringField()
    product_id = StringField()
    product_name = StringField()
    product_color= StringField()
    material=DictField()
    quantity=DictField()
    details_string= StringField()
    specification=DictField()
    price = IntField()
    wasprice = IntField()
    product_type=StringField()
    breadcrumb = StringField()
    stock = StringField()
    image = ListField(StringField())


class ProductFailedItem(DynamicDocument):
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_URL_FAILED}
    url = StringField(required=True)
   
    
    
