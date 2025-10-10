import csv
import logging
from settings import DATA_COLLECTION, file_name, FILE_HEADERS, db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class Export:
    """Exporting parsed FirstWeber agent data to CSV."""

    def __init__(self, writer):
        self.mongo = db  # MongoDB connection from settings
        self.writer = writer

    def start(self):
        """Export all documents as CSV."""

        # Write CSV header
        self.writer.writerow(FILE_HEADERS)
        logging.info("Export started — writing headers...")

        # Fetch all records from MongoDB
        for item in self.mongo[DATA_COLLECTION].find(no_cursor_timeout=True):
            profile_url = item.get("profile_url", "")
            first_name = item.get("first_name", "")
            middle_name = item.get("middle_name", "")
            last_name = item.get("last_name", "")
            title = (", ".join(item.get("title", [])) if isinstance(item.get("title"), list) else item.get("title", "")).replace("®","")
            description = item.get("description", "")
            address = item.get("address", "")
            street_address = item.get("street_address", "")
            city = item.get("city", "")
            state = item.get("state", "")
            zip_code = item.get("zip_code", "")
            country = item.get("country", "")
            languages = item.get("languages", "")
            website = item.get("website", "")
            social_links = ", ".join(item.get("social", [])) if isinstance(item.get("social"), list) else item.get("social", "")
            image_url = item.get("image_url", "")
            agent_phone_numbers = ", ".join(item.get("agent_phone_numbers", [])) if isinstance(item.get("agent_phone_numbers"), list) else item.get("agent_phone_numbers", "")

            data = [
                profile_url,
                first_name,
                middle_name,
                last_name,
                title,
                description,
                address,
                street_address,
                city,
                state,
                zip_code,
                country,
                languages,
                website,
                social_links,
                image_url,
                agent_phone_numbers,
            ]

            self.writer.writerow(data)
        logging.info(" Export completed successfully.")


if __name__ == "__main__":
    # Define CSV file name and headers
    FILE_HEADERS = [
        "profile_url",
        "first_name",
        "middle_name",
        "last_name",
        "title",
        "description",
        "address",
        "street_address",
        "city",
        "state",
        "zip_code",
        "country",
        "languages",
        "website",
        "social_links",
        "image_url",
        "agent_phone_numbers",
    ]

    with open(file_name, "w", encoding="utf-8", newline="") as file:
        writer_file = csv.writer(file, delimiter=",", quotechar='"')
        export = Export(writer_file)
        export.start()
        file.close()
