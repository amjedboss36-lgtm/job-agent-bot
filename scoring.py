from filters import detect_benefits

def calculate_score(job):

    score = 0

    title = (job.get("title") or "").lower()

    if any(x in title for x in [
        "nurse",
        "nursing",
        "caregiver",
        "healthcare assistant",
        "care assistant"
    ]):
        score += 50

    elif any(x in title for x in [
        "admin",
        "administration",
        "office",
        "business"
    ]):
        score += 30

    else:
        score += 15

    benefits = detect_benefits(job.get("description", ""))

    if benefits["visa"]:
        score += 20

    if benefits["relocation"]:
        score += 10

    if benefits["training"]:
        score += 10

    if benefits["international"]:
        score += 10

    country = (job.get("country") or "").lower()

    europe_keywords = [
        "germany",
        "netherlands",
        "sweden",
        "norway",
        "denmark",
        "france",
        "belgium",
        "austria"
    ]

    gulf_keywords = [
        "saudi",
        "uae",
        "qatar",
        "oman",
        "kuwait",
        "bahrain"
    ]

    if any(x in country for x in europe_keywords):
        score += 10

    elif any(x in country for x in gulf_keywords):
        score += 8

    return min(score, 100)
