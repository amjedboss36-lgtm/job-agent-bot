import requests
from job_normalizer import normalize_job

HEADERS = {"User-Agent": "Mozilla/5.0"}


# =========================
# RemoteOK API (قوي جدًا)
# =========================
def remoteok_jobs():
    jobs = []

    try:
        url = "https://remoteok.com/api"
        r = requests.get(url, headers=HEADERS, timeout=20)
        data = r.json()

        for item in data:
            if not isinstance(item, dict):
                continue

            jobs.append(
                normalize_job(
                    item.get("position"),
                    item.get("url"),
                    item.get("location", "Remote"),
                    item.get("description", ""),
                    "RemoteOK"
                )
            )

    except:
        pass

    return jobs


# =========================
# Arbeitnow API (أوروبا)
# =========================
def arbeitnow_jobs():
    jobs = []

    try:
        url = "https://www.arbeitnow.com/api/job-board-api"
        r = requests.get(url, headers=HEADERS, timeout=20)
        data = r.json()

        for item in data.get("data", []):
            jobs.append(
                normalize_job(
                    item.get("title"),
                    item.get("url"),
                    "Europe",
                    item.get("description", ""),
                    "Arbeitnow"
                )
            )

    except:
        pass

    return jobs


# =========================
# Main collector
# =========================
def collect_all_jobs():

    jobs = []
    jobs.extend(remoteok_jobs())
    jobs.extend(arbeitnow_jobs())

    return jobs
