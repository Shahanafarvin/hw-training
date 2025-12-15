from mongoengine import DynamicDocument, StringField, IntField

from settings import MONGO_COLLECTION_CATEGORY,MONGO_COLLECTION_PRODUCTS, MONGO_COLLECTION_DATA

class ProductItem(DynamicDocument):
    """initializing URL fields and its Data-Types"""
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_PRODUCTS}
    product_url = StringField(required=True)
    product_name= StringField()
    selling_price= StringField()
    discount=StringField()
    regular_price=StringField()
    match_type=StringField()
    ean=StringField()
    cnk=StringField()
    score=IntField()


class ProductDataItem(DynamicDocument):
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_DATA}
    
    product_url=StringField()
    breadcrumbs=StringField()
    product_name=StringField()
    selling_price=StringField()
    discount=StringField()
    regular_price=StringField()
    reviews=StringField()
    package_size=StringField()
    price_per_size=StringField()
    details=StringField()
    product_descriptioN=StringField()
    rating=StringField()
    images=StringField()
    match_type=StringField()
    ean=StringField()
    cnk=StringField()
    score=IntField()

class ProductFailedItem(DynamicDocument):
    meta = {"db_alias": "default", "collection": MONGO_COLLECTION_DATA}
    
    url=StringField()
    status_code=StringField()
    error=StringField()