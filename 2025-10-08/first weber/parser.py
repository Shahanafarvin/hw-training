import time
import random
from curl_cffi import requests
from lxml import html
from urllib.parse import urljoin
from settings import BASE_URL, HEADERS, MAX_URLS, urls_collection, data_collection


class FirstWeberParser:
    """Parser for FirstWeber agent details."""

    def __init__(self):
        self.total_requests = 0
        self.success_count = 0
        self.failure_count = 0

    def parse_agents(self):
        """Fetch each agent URL and extract details."""

        # Load URLs from MongoDB
        urls = [doc["url"] for doc in urls_collection.find({}, {"url": 1})]
        agent_urls = urls[:MAX_URLS]

        print(f"Loaded {len(agent_urls)} URLs from MongoDB")

        for url in agent_urls:
            self.total_requests += 1
            try:
                resp = requests.get(url, headers=HEADERS, impersonate="chrome", timeout=60)
                if resp.status_code == 200:
                    self.success_count += 1
                    data = self.extract_profile(resp.text, url)
                    data_collection.insert_one(data)
                    print(f"Saved: {data.get('first_name', '')} {data.get('last_name', '')}")
                else:
                    self.failure_count += 1
                    print(f"Failed ({resp.status_code}): {url}")
            except Exception as e:
                self.failure_count += 1
                print(f"Error ({url}): {e}")

            # Random polite delay between 1.5 and 2 seconds
            time.sleep(random.uniform(1.5, 2.0))

    def extract_profile(self, html_text, url):
        """Extract agent profile details from HTML."""

        tree = html.fromstring(html_text)
        profile = {"profile_url": url}

        name = tree.xpath('//p[@class="rng-agent-profile-contact-name"]/text()')
        name = name[0].strip() if name else ""
        profile["first_name"] = name.split()[0] if name else ""
        profile["middle_name"] = " ".join(name.split()[1:-1]) if len(name.split()) > 2 else ""
        profile["last_name"] = name.split()[-1] if len(name.split()) > 1 else ""

        image = tree.xpath('//img[@class="rng-agent-profile-photo"]/@src')
        profile["image_url"] = urljoin(BASE_URL, image[0]) if image else ""

        address = tree.xpath('//li[@class="rng-agent-profile-contact-address"]//text()')
        address = " | ".join([a.strip() for a in address if a.strip()]) if address else ""
        profile["address"] = address

        desc = tree.xpath('//div[contains(@id,"widget-text-1-preview-")]/text()')
        profile["description"] = desc[0].strip() if desc else ""

        langs = tree.xpath('//p[@class="rng-agent-profile-languages" and small[contains(text(),"Languages Spoken")]]/text()')
        langs = [l.strip() for l in langs if l.strip()]
        profile["languages"] = langs[0] if langs else ""

        profile["social"] = tree.xpath('//li[@class="rng-agent-profile-contact-social"]//li/a/@href') or []
        website = tree.xpath('//li[@class="rng-agent-profile-contact-website"]/a/@href')
        profile["website"] = website[0] if website else ""

        title = tree.xpath('//p[@class="rng-agent-profile-languages" and small[contains(text(),"Designations")]]/text()')
        profile["title"] = title if title else ""

        lines = [line.strip() for line in address.split("|") if line.strip()]
        street_address = lines[0] if len(lines) > 0 else ""
        city = state = zipcode = ""
        country = "USA"

        if len(lines) > 1:
            parts = lines[1].split()
            if len(parts) >= 3:
                city = " ".join(parts[:-2])
                state = parts[-2]
                zipcode = parts[-1]

        profile.update({
            "street_address": street_address,
            "city": city,
            "state": state,
            "zip_code": zipcode,
            "country": country,
            "agent_phone_numbers": [p.strip() for p in tree.xpath('//a[starts-with(@href,"tel:")]/text()')] or []
        })

        return profile


if __name__ == "__main__":
    parser = FirstWeberParser()
    parser.parse_agents()
