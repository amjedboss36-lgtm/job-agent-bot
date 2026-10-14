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
# LangSearch: free full-web search provider (API key required)
# =========================
def langsearch_web_jobs():
    import os

    token = os.getenv("LANGSEARCH_API_KEY", "").strip()
    if not token:
        print("LangSearch skipped: LANGSEARCH_API_KEY not configured")
        return []

    # Focus on realistic opportunities aligned with nursing, healthcare/business
    # administration, operations and entry-level roles; avoid generic trading noise.
    queries = [
        "nursing jobs visa sponsorship official hospital careers page",
        "registered nurse staff nurse healthcare assistant visa sponsorship",
        "hospital administration healthcare administration jobs entry level",
        "business administration assistant operations coordinator logistics jobs",
        "customer service administrative assistant data entry jobs visa sponsorship",
        "site:linkedin.com/jobs nursing OR healthcare administration visa sponsorship",
        "site:facebook.com nurse nursing hospital jobs vacancy hiring",
        "site:instagram.com nurse nursing hospital jobs vacancy hiring",
        "site:*.com/careers nurse hospital administrator operations assistant",
        "site:*.org/jobs nurse healthcare administration vacancy",
        "site:*.gov/jobs nurse healthcare administration vacancy",
        "international recruitment hospital nursing jobs official employer",
    ]
    jobs = []
    seen = set()
    endpoint = "https://api.langsearch.com/v1/web-search"
    headers = {**HEADERS, "Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"}

    for query in queries:
        try:
            response = requests.post(
                endpoint,
                json={"query": query, "count": 10},
                headers=headers,
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
            data = payload.get("data") or {}
            pages = data.get("webPages") or data.get("web_pages") or payload.get("webPages") or {}
            items = pages.get("value") or pages.get("results") or data.get("results") or []
            for item in items:
                title = (item.get("name") or item.get("title") or "").strip()
                link = (item.get("url") or item.get("link") or "").strip()
                snippet = (item.get("snippet") or item.get("text") or item.get("description") or "").strip()
                if not title or not link.startswith(("https://", "http://")) or link in seen:
                    continue
                seen.add(link)
                jobs.append(normalize_job(
                    title, link,
                    item.get("siteName") or item.get("displayUrl") or "LangSearch",
                    snippet, "LangSearch Web Search",
                ))
        except Exception as exc:
            print(f"LangSearch failed for query {query!r}: {exc}")

    print(f"LangSearch web search: {len(jobs)} unique results")
    return jobs


# =========================
# Brave Search: full-web search provider
# Recommended for new setups; Google Custom Search JSON API is closed to new
# customers. Uses the account token only when BRAVE_SEARCH_API_KEY is configured.
# =========================
def brave_web_jobs():
    import os

    token = os.getenv("BRAVE_SEARCH_API_KEY", "").strip()
    if not token:
        print("Brave Search skipped: BRAVE_SEARCH_API_KEY not configured")
        return []

    # Focus on realistic opportunities aligned with nursing, healthcare/business
    # administration, operations and entry-level roles; avoid generic trading noise.
    queries = [
        "nursing jobs visa sponsorship official hospital careers page",
        "registered nurse staff nurse healthcare assistant visa sponsorship",
        "hospital administration healthcare administration jobs entry level",
        "business administration assistant operations coordinator logistics jobs",
        "customer service administrative assistant data entry jobs visa sponsorship",
        "site:linkedin.com/jobs nursing OR healthcare administration visa sponsorship",
        "site:facebook.com nurse nursing hospital jobs vacancy hiring",
        "site:instagram.com nurse nursing hospital jobs vacancy hiring",
        "site:*.com/careers nurse hospital administrator operations assistant",
        "site:*.org/jobs nurse healthcare administration vacancy",
        "site:*.gov/jobs nurse healthcare administration vacancy",
        "international recruitment hospital nursing jobs official employer",
    ]
    jobs = []
    seen = set()
    endpoint = "https://api.search.brave.com/res/v1/web/search"

    for query in queries:
        try:
            response = requests.get(
                endpoint,
                params={"q": query, "count": 10},
                headers={**HEADERS, "X-Subscription-Token": token, "Accept": "application/json"},
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
            for item in (payload.get("web") or {}).get("results", []):
                title = (item.get("title") or "").strip()
                link = (item.get("url") or "").strip()
                snippet = (item.get("description") or "").strip()
                if not title or not link.startswith(("https://", "http://")) or link in seen:
                    continue
                seen.add(link)
                jobs.append(
                    normalize_job(
                        title,
                        link,
                        item.get("profile", {}).get("long_name", "Unknown"),
                        snippet,
                        "Brave Web Search",
                    )
                )
        except Exception as exc:
            print(f"Brave web search failed for query {query!r}: {exc}")

    print(f"Brave web search: {len(jobs)} unique results")
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
    jobs.extend(langsearch_web_jobs())
    jobs.extend(brave_web_jobs())
    jobs.extend(google_web_jobs())

    return jobs
