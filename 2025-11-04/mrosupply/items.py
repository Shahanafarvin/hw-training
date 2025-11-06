# items.py
from mongoengine import Document, StringField, ListField, IntField, FloatField
from settings import (
    MONGO_COLLECTION_CATEGORY,
    MONGO_COLLECTION_PRODUCTS,
    MONGO_COLLECTION_DATA,
)          

class CategoryItem(Document):
    """MongoEngine model for category tree."""
    meta = {'collection': MONGO_COLLECTION_CATEGORY}
    name = StringField(required=True)
    url = StringField(required=True)
    subcategories = ListField()  

class ProductUrlItem(Document):
    """MongoEngine model for saving product URLs for each category."""
    meta = {'collection': MONGO_COLLECTION_PRODUCTS}
    category_name = StringField(required=True)
    category_url = StringField(required=True)
    product_urls = ListField(StringField())

class ProductDetailItem(Document):
    """MongoEngine model for saving detailed product information."""
    meta = {'collection': MONGO_COLLECTION_DATA}
    Item_Name = StringField()
    Brand_Name = StringField()
    Manufacturer_Name = StringField()
    Vendor_Seller_Part_Number = IntField()
    Manufacturer_Part_Number = StringField()
    Price = FloatField()
    Availability = StringField()
    QTY_Per_UOI = StringField()
    Product_Category = StringField()
    Company_Name = StringField()
    URL = StringField(required=True, unique=True)
    Full_Product_Description = StringField()
    Model_Number = StringField()