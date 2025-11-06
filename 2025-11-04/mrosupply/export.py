import csv
from pymongo import MongoClient
from settings import (
    MONGO_DB,
    logging,
    FILE_NAME,
    FILE_HEADERS,
    MONGO_COLLECTION_DATA
)


class Export:
    """Export MRO Supply data from MongoDB to CSV"""

    def __init__(self, writer):
        client = MongoClient("mongodb://localhost:27017/")
        self.mongo = client[MONGO_DB]
        self.writer = writer

    def start(self):
        """Export all product data"""
        self.writer.writerow(FILE_HEADERS)
        logging.info(" CSV headers written successfully.")

        cursor = self.mongo[MONGO_COLLECTION_DATA].find(no_cursor_timeout=True)

        for item in cursor:
            try:
                def clean_text(value):
                    """Cleans and normalizes text fields"""
                    if isinstance(value, list):
                        return "; ".join([str(v).strip() for v in value if v])
                    if isinstance(value, dict):
                        return "; ".join([f"{k}: {v}" for k, v in value.items()])
                    return str(value).replace("\n", " ").replace("\r", " ").strip() if value else ""

                def format_price(value):
                    """Ensure price formatting"""
                    try:
                        return f"{float(value):.2f}"
                    except (TypeError, ValueError):
                        return value or ""

                cleaned = {
                    "Company Name": clean_text(item.get("Company_Name", "MRO Supply")),
                    "Manufacturer Name": clean_text(item.get("Manufacturer_Name", "")),
                    "Brand Name": clean_text(item.get("Brand_Name", "")),
                    "Vendor/Seller Part Number": clean_text(item.get("Vendor_Seller_Part_Number", "")),
                    "Item Name": clean_text(item.get("Item_Name", "")),
                    "Full Product Description": clean_text(item.get("Full_Product_Description", "")),
                    "Price": format_price(item.get("Price", "")),
                    "Unit of Issue": "",
                    "QTY Per UOI": clean_text(item.get("QTY_Per_UOI", "")),
                    "Product Category": clean_text(item.get("Product_Category", "")).replace(",", " > "),
                    "URL": clean_text(item.get("URL", "")),
                    "Availability": clean_text(item.get("Availability", "")),
                    "Manufacturer Part Number": clean_text(item.get("Manufacturer_Part_Number", "")),
                    "Country of Origin": "",
                    "UPC": "",
                    "Model Number": clean_text(item.get("Model_Number", "")),
                }

                # Write CSV row
                self.writer.writerow([cleaned.get(f, "") for f in FILE_HEADERS])

            except Exception as e:
                logging.error(f" Error processing record {item.get('_id')}: {e}")

        cursor.close()
        logging.info(" Export completed successfully.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    with open(FILE_NAME, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, quotechar='"')
        export = Export(writer)
        export.start()

    logging.info(f" Data exported successfully to {FILE_NAME}")
