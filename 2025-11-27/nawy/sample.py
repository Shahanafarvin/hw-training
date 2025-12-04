import json
import logging
from pymongo import MongoClient
from settings import MONGO_DB, FILE_NAME, FILE_HEADER, MONGO_COLLECTION_DATA


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")

class Export:
    """Export ProductItem collection to JSON"""

    def __init__(self, file_handle):
        self.file_handle = file_handle
        self.client = MongoClient("localhost", 27017)
        self.db = self.client[MONGO_DB]

    def start(self):
        """Export as JSON file (one object per line)"""
        logging.info("Starting export...")
        
        count = 0
        max_records = 200

        for item in self.db[MONGO_COLLECTION_DATA].find(no_cursor_timeout=True).limit(max_records):
            url= item.get("url")
            title= item.get("title","")
            location=item.get("location","")
            price=item.get("price","")
            max_price=item.get("max_price","")
            type_ = item.get("type","")
            property_type=item.get("property_type","")
            details=item.get("details","")
            reference_number=item.get("reference_number","")
            bedrooms=item.get("bedrooms","")
            bathrooms=item.get("bathrooms","")
            delivery_in=item.get("delivery_in","")
            compound=item.get("compound","")
            sale_type=item.get("sale_type","")
            finishing=item.get("finishing","")
            ready_by=item.get("ready_by","")
            iteration_number=item.get("iteration_number","")
            date = item.get("date","") 
            
            data = {
                "url" : url,
                "title" : title,
                "location" : location,
                "price" : price,
                "max_price" : max_price,
                "type" : type_,
                "property_type" : property_type,
                "details" : details,
                "reference_number" : reference_number,
                "bedrooms" : bedrooms,
                "bathrooms" : bathrooms,
                "delivery_in" : delivery_in,
                "compound" : compound,
                "sale_type" : sale_type,
                "finishing" : finishing,
                "ready_by" : ready_by,
                "iteration_number" :iteration_number,
                "date" : date
                        }

            # Write one JSON object per line
            self.file_handle.write(json.dumps(data, ensure_ascii=False) + "\n")
            count += 1
            logging.info(f"Exported ({count}/{max_records}): {item.get('title')}")
        
        logging.info(f"Export completed. Total records: {count}")
            

if __name__ == "__main__":
    # Change file extension to .json or update FILE_NAME in settings
    json_file_name = FILE_NAME.replace('.csv', '.json') if '.csv' in FILE_NAME else FILE_NAME + '.json'
    
    with open(json_file_name, "w", encoding="utf-8") as file:
        export = Export(file)
        export.start()