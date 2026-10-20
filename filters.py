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
    if host == "eures.europa.eu" or host.endswith(".eures.europa.eu") or host.startswith("eures.europa.eu."):
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



# Results that explain how to find jobs are not themselves vacancies.
# Keep this deliberately conservative: only reject clear editorial titles or
# known article-style pages, not ordinary employer career pages.
import re


_INFORMATIONAL_TITLE_PATTERNS = (
    r"^how to\b",
    r"^a guide to\b",
    r"^the ultimate guide\b",
    r"^guide to\b",
    r"^tips for\b",
    r"^everything you need to know\b",
    r"^steps to\b",
    r"^how .* apply\b",
    r"^how .* get .* visa sponsorship\b",
)


def is_informational_result(title, url, description=""):
    """Return True for obvious job-search articles rather than specific vacancies."""
    title_text = " ".join(str(title or "").split()).lower()
    description_text = " ".join(str(description or "").split()).lower()
    try:
        parsed = urlparse(str(url or "").strip())
        host = (parsed.hostname or "").lower().rstrip(".")
        path = parsed.path.lower()
    except (TypeError, ValueError):
        host, path = "", ""

    if any(re.search(pattern, title_text) for pattern in _INFORMATIONAL_TITLE_PATTERNS):
        return True

    # Editorial and marketing sites are useful as background reading, but are
    # not employers or direct vacancy listings.
    if host == "leverageedu.com" or host.endswith(".leverageedu.com"):
        return True

    # The dated Blogspot page in the reported false positives is a general
    # sponsorship roundup, not a named vacancy. Do not blanket-block all blogs.
    if (host.endswith(".blogspot.com") and re.search(r"/20\d{2}/\d{1,2}/", path)
            and "visa sponsorship" in title_text
            and not re.search(r"\b(nurse|nursing|registered nurse|administrator|assistant|technician|driver|accountant|receptionist)\b", title_text)):
        return True

    # A raw cloud-compute hostname is not enough to establish employer identity;
    # reject it when paired with an editorial/how-to result.
    if host.endswith(".compute.amazonaws.com") and (
        "how to" in title_text or "visa sponsorship" in title_text and "apply" in title_text
    ):
        return True

    # Snippets that only advertise a guide, with no vacancy-specific wording,
    # should not be promoted as jobs.
    editorial_phrases = (
        "how to apply for", "step-by-step guide", "complete guide to",
        "everything you need to know about", "tips to find a job",
    )
    return any(phrase in description_text for phrase in editorial_phrases) and not re.search(
        r"\b(apply now|submit application|job id|vacancy closes|closing date|requisition)\b",
        description_text,
    )
