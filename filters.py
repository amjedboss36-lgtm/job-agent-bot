from urllib.parse import urlparse

BAD_PATTERNS = [
    "eures.europa.eu"
]

def is_valid_job_link(url):
    if not url:
        return False

    parsed = urlparse(str(url).strip())
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False

    host = parsed.hostname.lower().rstrip(".")
    if host == "eures.europa.eu" or host.endswith(".eures.europa.eu"):
        return False

    # Reject lookalike / malformed hosts and embedded credentials.
    if parsed.username or parsed.password or "." not in host:
        return False

    return True


def is_target_job(text):
    text = (text or "").lower()

    keywords = [
        "nurse", "nursing", "caregiver",
        "care assistant", "healthcare", "hospital", "medical",
        "warehouse", "hotel", "hospitality", "restaurant", "chef",
        "waiter", "admin", "office", "secretary", "data entry",
        "receptionist", "customer service", "logistics", "inventory",
        "operator", "technician", "cleaner", "driver", "sales",
        "accounting", "finance", "human resources", "hr", "marketing",
        "IT support", "software", "remote", "entry level", "trainee"
    ]

    return any(k in text for k in keywords)


def detect_benefits(text):
    text = (text or "").lower()

    return {
        "visa": "visa" in text or "sponsorship" in text,
        "relocation": "relocation" in text,
        "training": "training" in text,
        "international": "international" in text or "overseas" in text
    }


def detect_requirements(text):
    text = (text or "").lower()

    high_demand_keywords = [
        "phd", "senior", "5+ years", "10 years",
        "expert", "lead", "manager", "director"
    ]

    low_entry_keywords = [
        "no experience",
        "entry level",
        "training provided",
        "junior",
        "fresh graduate",
        "we train"
    ]

    return {
        "high_demand": any(x in text for x in high_demand_keywords),
        "low_entry": any(x in text for x in low_entry_keywords)
    }
