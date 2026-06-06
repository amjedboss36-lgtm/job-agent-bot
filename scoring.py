from filters import detect_benefits, detect_requirements


def calculate_score(job):

    score = 0

    title = (job.get("title") or "").lower()
    desc = (job.get("description") or "").lower()
    text = title + " " + desc

    benefits = detect_benefits(text)
    requirements = detect_requirements(text)

    # =========================
    # 1. VISA / SPONSORSHIP (أولوية قصوى)
    # =========================
    if benefits["visa"]:
        score += 40
    else:
        score -= 20  # يقلل الوظائف بدون فيزا

    if benefits["relocation"]:
        score += 15

    if benefits["international"]:
        score += 10

    # =========================
    # 2. مستوى المتطلبات
    # =========================
    if requirements["low_entry"]:
        score += 30

    if requirements["high_demand"]:
        score -= 25

    # =========================
    # 3. نوع الوظيفة
    # =========================
    if any(x in title for x in [
        "nurse", "caregiver", "healthcare", "assistant"
    ]):
        score += 20

    if any(x in title for x in [
        "warehouse", "hotel", "cleaner", "worker"
    ]):
        score += 15

    # =========================
    # 4. حد نهائي
    # =========================
    score = max(0, min(score, 100))

    return score
