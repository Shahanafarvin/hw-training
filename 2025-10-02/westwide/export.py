
import json
from pymongo import MongoClient

def export_to_json(mongo_uri="mongodb://localhost:27017/",
                   db_name="westside",
                   collection_name="products",
                   output_file="products.json"):
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]

    # Fetch all documents, exclude _id
    data = list(collection.find({}, {"_id": 0}))

    # Write to JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"Exported {len(data)} records to {output_file}")

if __name__ == "__main__":
    export_to_json()
