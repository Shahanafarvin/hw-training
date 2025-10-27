from mongoengine import DynamicDocument, StringField, ListField, DictField, IntField, FloatField, URLField, Document, EmbeddedDocument, EmbeddedDocumentField
from settings import MONGO_COLLECTION_CATEGORY, MONGO_COLLECTION_DATA

class SubCategory(EmbeddedDocument):
    category_id = IntField(required=True)
    category_name = StringField(required=True)
    child_count = IntField(default=0)
    category_api = URLField()
    category_products_api = URLField()
    subcategories = ListField(EmbeddedDocumentField('SubCategory'))  # recursive subcategories

class ProductCategoryItem(Document):

    meta = {"collection": MONGO_COLLECTION_CATEGORY}
    category_id = IntField(required=True)
    category_name = StringField(required=True)
    child_count = IntField(default=0)
    category_api = URLField()
    category_products_api = URLField()
    subcategories = ListField(EmbeddedDocumentField(SubCategory)) # Each dict: sub_id, sub_name, sub_product_count, subcategory_api

class ProductItem(DynamicDocument):
    """Store product details from subcategory APIs"""
    meta = {"collection": MONGO_COLLECTION_DATA}  

    product_url = StringField(required=True, unique=True)
    title = StringField()
    brand = StringField()
    breadcrumbs = StringField()
    images = ListField(StringField())
    grammage_quantity = FloatField()
    grammage_unit = StringField()
    unit_price = FloatField()
    regular_price = FloatField()
    currency = StringField()
    sku = IntField()
    product_id = IntField()
    selectvalue = IntField()
    details = ListField()
    rating = FloatField()
    review = IntField()


    # --- Parser-collected details ---
    description = StringField()
    parameters = ListField(DictField())
    ingredients = StringField()
    nutrition = ListField(DictField())
    allergens = StringField()