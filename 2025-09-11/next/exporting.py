import json
import pandas as pd
import pymongo

# ---------------- MongoDB Read ---------------- #
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["nextdb"]
col = db["product_details"]

docs = list(col.find({}, {"_id": 0}))  # exclude MongoDB _id

# ---------------- JSON ARRAY ---------------- #
with open("products_array.json", "w", encoding="utf-8") as f:
    json.dump(docs, f, ensure_ascii=False, indent=4)

# ---------------- JSON LINES ---------------- #
with open("products_lines.jsonl", "w", encoding="utf-8") as f:
    for doc in docs:
        f.write(json.dumps(doc, ensure_ascii=False) + "\n")

# ---------------- CSV (Normal) ---------------- #
df = pd.DataFrame(docs)
df.to_csv("products.csv", index=False, encoding="utf-8")

# ---------------- Pipe-Separated CSV ---------------- #
df.to_csv("products_pipe.csv", index=False, sep="|", encoding="utf-8")

print(" Export completed: JSON array, JSON lines, CSV, and Pipe CSV saved.")

# ---------------- Conversions ---------------- #

# JSON Array -> CSV
df = pd.read_json("products_array.json")
df.to_csv("converted_from_json.csv", index=False)

print("Conversions completed: All formats transformed successfully.")
