from mongoengine import (
    DynamicDocument,
    StringField,
    ListField,
    DictField,
    DateTimeField,
    
)
from settings import (
    MONGO_COLLECTION_CATEGORY,
    MONGO_COLLECTION_PRODUCT_URLS,
    MONGO_COLLECTION_PRODUCT_DETAILS
)


class CategoryItem(DynamicDocument):
    """Category with subcategories"""
    meta = {"collection": MONGO_COLLECTION_CATEGORY}
    category = StringField(required=True)
    url = StringField(required=True)
    subcategories = ListField(DictField())  
   


class ProductUrlItem(DynamicDocument):
    """Single product URL entry saved by crawler"""
    meta = {"collection": MONGO_COLLECTION_PRODUCT_URLS}
    category = StringField()
    subcategory = StringField()
    url = StringField(required=True)
    


class ProductItem(DynamicDocument):
    """Product detail saved by parser"""
    meta = {"collection": MONGO_COLLECTION_PRODUCT_DETAILS}
    url = StringField(required=True)
    breadcrumbs = ListField(StringField())
    product_name = StringField()
    price = StringField()
    oem_part_for = StringField()
    part_number = StringField()
    availability = StringField()
    description = StringField()
    additional_description = StringField()
    
