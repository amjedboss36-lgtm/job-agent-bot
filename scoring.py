from filters import detect_benefits


def calculate_score(job):

    score = 0

    text = (job.get("title", "") + " " + job.get("description", "")).lower()
    country = (job.get("country") or "").lower()

    # =========================
    # 🎫 VISA PRIORITY (أهم جزء)
    # =========================
    visa_keywords = [
        "visa sponsorship",
        "sponsorship",
        "work permit",
        "relocation",
        "immigration support",
        "migrate",
        "foreign workers",
        "international applicants"
    ]

    if any(k in text for k in visa_keywords):
        score += 60
    elif "remote" in text:
        score += 25
    else:
        score += 10


    # =========================
    # 🧠 EASY REQUIREMENTS
    # =========================
    easy_keywords = [
        "no experience",
        "entry level",
        "training provided",
        "no degree",
        "junior",
        "basic english"
    ]

    if any(k in text for k in easy_keywords):
        score += 20


    # =========================
    # 🌍 COUNTRIES (Migration Friendly)
    # =========================
    good_countries = [
        "germany", "netherlands", "sweden",
        "norway", "denmark", "canada",
        "australia", "uk", "ireland"
    ]

    if any(c in country for c in good_countries):
        score += 15


    # =========================
    # 📦 BENEFITS (من detect_benefits)
    # =========================
    benefits = detect_benefits(text)

    if benefits["visa"]:
        score += 15

    if benefits["relocation"]:
        score += 10

    if benefits["training"]:
        score += 5

    if benefits["international"]:
        score += 5


    return min(score, 100)
