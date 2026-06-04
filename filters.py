import requests

BAD_PATTERNS = [
    "eures.europa.eu",
    "/jobs",
    "/careers",
    "/vacancies",
    "/search",
    "/find-jobs"
]

def is_valid_job_link(url):
    if not url:
        return False

    url = url.lower()

    # ❗ لا نقتل الوظائف بسبب status code (مهم جدًا)
    if "http" not in url:
        return False

    if "eures.europa.eu" in url:
        return False

    for p in BAD_PATTERNS:
        if p in url:
            return False

    return True  # 🔥 أهم تعديل: قبول الروابط أولاً


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
