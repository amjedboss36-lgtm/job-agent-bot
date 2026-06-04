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

    lower = url.lower().strip()

    if lower == "https://eures.europa.eu":
        return False

    try:
        response = requests.get(
            url,
            timeout=15,
            allow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        if response.status_code != 200:
            return False

        final_url = response.url.lower()

        if final_url == "https://eures.europa.eu":
            return False

        for pattern in BAD_PATTERNS:
            if final_url.endswith(pattern):
                return False

        page = response.text.lower()

        indicators = [
            "apply",
            "apply now",
            "job description",
            "responsibilities",
            "requirements",
            "qualifications"
        ]

        score = 0

        for indicator in indicators:
            if indicator in page:
                score += 1

        return score >= 2

    except Exception:
        return False


def is_target_job(text):
    text = (text or "").lower()

    keywords = [
        "nurse",
        "nursing",
        "caregiver",
        "care assistant",
        "healthcare assistant",
        "hospital",
        "health",
        "medical",

        "business",
        "administration",
        "office",
        "admin",
        "reception",

        "warehouse",
        "hotel",
        "factory",
        "worker",
        "seasonal",
        "farm"
    ]

    return any(k in text for k in keywords)


def detect_benefits(text):
    text = (text or "").lower()

    return {
        "visa": any(x in text for x in [
            "visa sponsorship",
            "sponsorship",
            "work permit"
        ]),

        "relocation": any(x in text for x in [
            "relocation",
            "relocation package"
        ]),

        "training": any(x in text for x in [
            "training",
            "language training",
            "apprenticeship"
        ]),

        "international": any(x in text for x in [
            "international applicants",
            "overseas applicants"
        ])
    }
