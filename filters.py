import requests

BAD_PATTERNS = [
    "eures.europa.eu"
]

def is_valid_job_link(url):
    if not url:
        return False

    url = url.lower()

    if "http" not in url:
        return False

    if "eures.europa.eu" in url:
        return False

    return True


def is_target_job(text):
    text = (text or "").lower()

    keywords = [
        "nurse", "nursing", "caregiver",
        "care assistant", "healthcare",
        "hospital", "medical",
        "warehouse", "hotel",
        "admin", "office", "worker",
        "assistant"
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
