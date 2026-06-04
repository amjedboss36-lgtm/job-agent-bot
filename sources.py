import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from filters import is_valid_job_link, is_target_job

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# =========================
# EURES (placeholder)
# =========================
def eures_jobs():
    """
    EURES is a conceptual source for now.
    """
    return []

# =========================
# Indeed RSS
# =========================
def indeed_jobs():
    jobs = []

    queries = [
        "nursing assistant visa sponsorship",
        "caregiver sponsorship europe",
        "healthcare assistant germany",
        "hospital jobs international",
        "warehouse worker relocation"
    ]

    for q in queries:
        try:
            url = "https://rss.indeed.com/rss?q=" + q.replace(" ", "+")
            r = requests.get(url, headers=HEADERS, timeout=20)

            root = ET.fromstring(r.text)

            for item in root.findall(".//item"):
                title = item.findtext("title")
                link = item.findtext("link")

                job = {
                    "title": title,
                    "link": link,
                    "country": "Indeed",
                    "description": title
                }

                if is_target_job(title) and is_valid_job_link(link):
                    jobs.append(job)

        except:
            continue

    return jobs

# =========================
# Healthcare / Care jobs
# =========================
def healthcare_career_jobs():

    sources = [
        {
            "title": "NHS Jobs (UK Healthcare Portal)",
            "link": "https://www.jobs.nhs.uk",
            "country": "UK",
            "description": "healthcare nursing hospital uk"
        },
        {
            "title": "International Nursing Programs",
            "link": "https://healthcareers.nhs.uk",
            "country": "UK",
            "description": "nursing international training"
        },
        {
            "title": "Care Home Opportunities Europe",
            "link": "https://www.prelude-innovation.com/careers",
            "country": "Europe",
            "description": "caregiver elderly care europe"
        }
    ]

    jobs = []

    for j in sources:
        if is_target_job(j["description"]):
            jobs.append(j)

    return jobs

# =========================
# Main collector
# =========================
def collect_all_jobs():
    jobs = []

    jobs.extend(indeed_jobs())
    jobs.extend(eures_jobs())
    jobs.extend(healthcare_career_jobs())

    return jobs
