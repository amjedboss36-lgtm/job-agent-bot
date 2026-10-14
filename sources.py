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
# Google web search: official employer pages + public social job posts
# Requires Google Programmable Search credentials in GOOGLE_CSE_API_KEY
# and GOOGLE_CSE_CX. Without credentials the existing public APIs continue
# to work normally.
# =========================
def google_web_jobs():
    import os

    api_key = os.getenv("GOOGLE_CSE_API_KEY", "").strip()
    engine_id = os.getenv("GOOGLE_CSE_CX", "").strip()
    if not api_key or not engine_id:
        print("Google web search skipped: credentials not configured")
        return []

    queries = [
        "nursing jobs visa sponsorship official careers page",
        "site:jobs.* nurse apply hospital careers",
        "site:linkedin.com/jobs nursing jobs visa sponsorship",
        "site:facebook.com nurse nursing jobs vacancy hiring",
        "site:instagram.com nurse nursing jobs vacancy hiring",
        "site:*.com/careers nurse nursing vacancy",
        "site:*.org/jobs nurse nursing vacancy",
        "site:*.gov/jobs nurse nursing vacancy",
    ]
    jobs = []
    seen = set()
    endpoint = "https://www.googleapis.com/customsearch/v1"

    for query in queries:
        try:
            response = requests.get(
                endpoint,
                params={"key": api_key, "cx": engine_id, "q": query, "num": 10},
                headers=HEADERS,
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
            for item in payload.get("items", []):
                title = (item.get("title") or "").strip()
                link = (item.get("link") or "").strip()
                snippet = (item.get("snippet") or "").strip()
                if not title or not link.startswith(("https://", "http://")) or link in seen:
                    continue
                seen.add(link)
                jobs.append(
                    normalize_job(
                        title,
                        link,
                        item.get("displayLink", "Unknown"),
                        snippet,
                        "Google Web Search",
                    )
                )
        except Exception as exc:
            print(f"Google web search failed for query {query!r}: {exc}")

    print(f"Google web search: {len(jobs)} unique results")
    return jobs


# =========================
# Main collector
# =========================
def collect_all_jobs():

    jobs = []
    jobs.extend(remoteok_jobs())
    jobs.extend(arbeitnow_jobs())
    jobs.extend(google_web_jobs())

    return jobs
