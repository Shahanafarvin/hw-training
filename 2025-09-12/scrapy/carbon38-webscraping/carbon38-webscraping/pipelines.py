import pymongo

class MongoPipeline:
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri="mongodb://localhost:27017",
            mongo_db="carbon38"
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        # Choose collection based on spider
        if spider.name == "product_urls":
            self.collection = self.db["product_urls"]
        elif spider.name == "product_data":
            self.collection = self.db["product_data"]
        else:
            self.collection = self.db["default_collection"]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.collection.update_one(
            {"product_url": item.get("product_url")},
            {"$set": item},
            upsert=True
        )
        return item
