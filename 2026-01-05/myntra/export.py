import csv
import json
import re
from html import unescape

INPUT_JSON = "/home/shahana/datahut-training/hw-training/myntra_complete_products.json"
OUTPUT_CSV = "/home/shahana/datahut-training/hw-training/myntra_products_export.csv"

# Base fields
base_headers = [
    "product_id",
    "product_url",
    "title",
    "brand",
    "breadcrumbs",
    "category",
    "gender",
    "regular_price",
    "selling_price",
    "discount",
    "promotion_description",
    "color",
    "sizes",
    "images",
    "rating",
    "reviews",
    "product_details"
]

# General cleaning function
def clean_value(val):
    if val is None:
        return ""
    val = str(val)
    val = unescape(val)           # remove HTML entities
    val = re.sub(r"<.*?>", "", val)  # remove HTML tags
    val = re.sub(r"\s+", " ", val)   # replace multiple spaces/newlines with single space
    return val.strip()

# Discount-specific cleaning
def clean_discount(val):
    if val is None:
        return ""
    val = str(val)
    match = re.search(r"(\d+)", val)
    return match.group(1) if match else ""

# Normalize field names for CSV headers (lowercase + spaces to _)
def normalize_field_name(field):
    return field.lower().replace(" ", "_")

# Function to flatten specifications
def flatten_specifications(specs, base_row):
    flat_row = base_row.copy()
    for k, v in specs.items():
        key = normalize_field_name(k)
        val = clean_value(v)
        if val.upper() == "NA":  # convert 'NA' to empty string
            val = ""
        flat_row[key] = val
    return flat_row
# Main export
if __name__ == "__main__":
    # Collect all unique specification fields
    spec_fields = set()
    products_data = []
    with open(INPUT_JSON, encoding="utf-8") as infile:
        for i, line in enumerate(infile):
            if i >= 200:  # limit to first 200 records
                break
            product = json.loads(line)
            specs = product.get("specifications", {})
            spec_fields.update([normalize_field_name(k) for k in specs.keys()])
            products_data.append(product)

    # Prepare final CSV headers
    final_headers = [normalize_field_name(f) for f in base_headers] + sorted(spec_fields)

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=final_headers, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()

        for product in products_data:
            row = {}
            for field in base_headers:
                val = product.get(field, "")
                if field == "discount":
                    row[normalize_field_name(field)] = clean_discount(val)
                else:
                    val = clean_value(val)
                    if field == "product_details":  # remove 'Product Details: ' only here
                        val = val.replace("Product Details: ", "")
                    row[normalize_field_name(field)] = val
            # Flatten specifications
            specs = product.get("specifications", {})
            row = flatten_specifications(specs, row)
            
            # Fill missing spec fields with empty string
            for sf in spec_fields:
                if sf not in row:
                    row[sf] = ""
            
            writer.writerow(row)
