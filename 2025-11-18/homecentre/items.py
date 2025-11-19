from mongoengine import Document, StringField, IntField, ListField, DictField
from settings import MONGO_PRODUCTS_COLLECTION, MONGO_DATA_COLLECTION      

class ProductUrlItem(Document):
    meta = {"collection": MONGO_PRODUCTS_COLLECTION}
    url = StringField(required=True, unique=True)
    category = StringField()      
    product_id = StringField() 
    product_name=StringField()
    details_string=StringField()
    price=IntField()
    wasprice=IntField()
    image=ListField()
    product_type=StringField()

class ProductItem(Document):
    meta = {"collection":MONGO_DATA_COLLECTION}
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
   
    
    
