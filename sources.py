import requests
import xml.etree.ElementTree as ET
from filters import is_target_job, detect_benefits

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# =========================
# EURES (placeholder)
# =========================
def eures_jobs():
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

                if not title or not link:
                    continue

                # فلترة مبدئية
                if not is_target_job(title):
                    continue

                benefits = detect_benefits(title)

                job = {
                    "title": title,
                    "link": link,
                    "country": "Indeed",
                    "description": title,
                    "benefits": benefits
                }

                jobs.append(job)

        except Exception:
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

        if not is_target_job(j["description"]):
            continue

        j["benefits"] = detect_benefits(j["description"])

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
