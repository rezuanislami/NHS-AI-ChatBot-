import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os

# 1. Approved URLs (manual whitelist)
approved_urls = [
    "https://www.careers.nhs.scot/explore-careers/administrative-services/",
    "https://www.careers.nhs.scot/explore-careers/allied-health-professions/",
    "https://www.careers.nhs.scot/explore-careers/ambulance-services/",
    "https://www.careers.nhs.scot/explore-careers/dental/",
    "https://www.careers.nhs.scot/explore-careers/health-play-services/",
    "https://www.careers.nhs.scot/explore-careers/healthcare-science/",
    "https://www.careers.nhs.scot/explore-careers/healthcare-support-workers/",
    "https://www.careers.nhs.scot/explore-careers/medical-associate-professions/",
    "https://www.careers.nhs.scot/explore-careers/medicine/",
    "https://www.careers.nhs.scot/explore-careers/midwifery/",
    "https://www.careers.nhs.scot/explore-careers/nhs-24-service-delivery/",
    "https://www.careers.nhs.scot/explore-careers/nursing/",
    "https://www.careers.nhs.scot/explore-careers/optometry/",
    "https://www.careers.nhs.scot/explore-careers/pharmacy/",
    "https://www.careers.nhs.scot/explore-careers/psychology/",
    "https://www.careers.nhs.scot/explore-careers/support-services/"
]

# 2. Output folder
os.makedirs("cleaned_pages", exist_ok=True)

def clean_text(text):
    lines = text.split("\n")
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)

for url in approved_urls:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # Remove unwanted tags
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        # Extract main content
        main_content = soup.find("main")

        if not main_content:
            print(f"Main content not found: {url}")
            continue

        text = main_content.get_text(separator="\n")
        cleaned_text = clean_text(text)

        # Metadata
        page_data = {
            "url": url,
            "title": soup.title.string if soup.title else "No Title",
            "scraped_date": datetime.now().strftime("%Y-%m-%d"),
            "content": cleaned_text
        }

        # Save as JSON
        file_name = url.rstrip("/").split("/")[-1] + ".json"
        file_path = os.path.join("cleaned_pages", file_name)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(page_data, f, ensure_ascii=False, indent=4)

        print(f"Saved: {file_name}")

    except Exception as e:
        print(f"Error scraping {url}: {e}")