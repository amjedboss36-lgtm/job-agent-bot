from filters import detect_benefits, detect_requirements


def calculate_score(job):
    """
    Enhanced scoring system with VISA-FIRST priority.
    
    Returns: dict with score (0-100) and priority_flags
    """
    
    score = 0
    priority_flags = []

    text = (job.get("title", "") + " " + job.get("description", "")).lower()
    country = (job.get("country") or "").lower()

    # =========================
    # 🔥 VISA SPONSORSHIP (HIGHEST PRIORITY)
    # =========================
    visa_keywords = [
        "visa sponsorship",
        "sponsorship",
        "work permit",
        "relocation",
        "immigration support",
        "migrate",
        "foreign workers",
        "international applicants",
        "visa support"
    ]

    if any(k in text for k in visa_keywords):
        score += 40
        priority_flags.append("VISA_SPONSORSHIP")
    elif "remote" in text:
        score += 20
        priority_flags.append("REMOTE_WORK")
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
        score += 15
        priority_flags.append("LOW_BARRIER_ENTRY")


    # =========================
    # 💼 JOB CATEGORY PRIORITY
    # =========================
    healthcare_keywords = [
        "nurse", "nursing", "caregiver", "care assistant",
        "healthcare", "hospital", "medical", "doctor",
        "pharmacist", "therapist", "mental health"
    ]

    hospitality_keywords = [
        "hotel", "restaurant", "chef", "waiter", "bartender",
        "hospitality", "accommodation", "tourism"
    ]

    admin_keywords = [
        "admin", "office", "assistant", "secretary",
        "data entry", "receptionist"
    ]

    if any(k in text for k in healthcare_keywords):
        score += 15
        priority_flags.append("HEALTHCARE_HIGH_DEMAND")

    elif any(k in text for k in hospitality_keywords):
        score += 10
        priority_flags.append("HOSPITALITY_OPPORTUNITY")

    elif any(k in text for k in admin_keywords):
        score += 5
        priority_flags.append("ADMIN_ROLE")


    # =========================
    # 🌍 COUNTRIES (Migration Friendly)
    # =========================
    excellent_countries = [
        "germany", "netherlands", "sweden",
        "norway", "denmark", "canada",
        "australia", "ireland", "switzerland",
        "singapore", "united arab emirates"
    ]

    good_countries = [
        "uk", "france", "spain", "italy",
        "belgium", "austria", "finland",
        "new zealand", "usa", "japan"
    ]

    if any(c in country for c in excellent_countries):
        score += 20
        priority_flags.append("EXCELLENT_DESTINATION")

    elif any(c in country for c in good_countries):
        score += 10
        priority_flags.append("GOOD_DESTINATION")


    # =========================
    # 📦 BENEFITS
    # =========================
    benefits = detect_benefits(text)

    if benefits["visa"]:
        score += 15
        priority_flags.append("VISA_BENEFIT")

    if benefits["relocation"]:
        score += 10
        priority_flags.append("RELOCATION_SUPPORT")

    if benefits["training"]:
        score += 5

    if benefits["international"]:
        score += 5
        priority_flags.append("INTERNATIONAL_FOCUS")


    # =========================
    # ⚠️ REQUIREMENT ADJUSTMENTS
    # =========================
    requirements = detect_requirements(text)

    if requirements["high_demand"]:
        score = max(0, score - 15)  # Reduce if highly demanding
        priority_flags.append("HIGH_DEMAND_ROLE")

    if requirements["low_entry"]:
        score += 10  # Boost if entry-level friendly
        priority_flags.append("ENTRY_LEVEL_FRIENDLY")


    # =========================
    # FINAL CAP & RETURN
    # =========================
    final_score = min(max(score, 0), 100)

    return {
        "score": final_score,
        "priority_flags": priority_flags
    }


def get_priority_emoji(flags):
    """Get emoji based on priority flags"""
    if "VISA_SPONSORSHIP" in flags:
        return "🎫"
    elif "HEALTHCARE_HIGH_DEMAND" in flags:
        return "⚕️"
    elif "REMOTE_WORK" in flags:
        return "💻"
    elif "EXCELLENT_DESTINATION" in flags:
        return "🌍"
    else:
        return "📌"


def format_flags_display(flags):
    """Format priority flags for display"""
    if not flags:
        return "No special flags"
    
    flag_emojis = {
        "VISA_SPONSORSHIP": "🎫 Visa Sponsorship",
        "REMOTE_WORK": "💻 Remote Work",
        "LOW_BARRIER_ENTRY": "✅ Easy Requirements",
        "HEALTHCARE_HIGH_DEMAND": "⚕️ Healthcare (High Demand)",
        "HOSPITALITY_OPPORTUNITY": "🏨 Hospitality",
        "ADMIN_ROLE": "📋 Admin Role",
        "EXCELLENT_DESTINATION": "🌍 Excellent Country",
        "GOOD_DESTINATION": "🌎 Good Country",
        "VISA_BENEFIT": "🎫 Visa Support",
        "RELOCATION_SUPPORT": "✈️ Relocation",
        "INTERNATIONAL_FOCUS": "🌐 International",
        "HIGH_DEMAND_ROLE": "⬆️ High Demand",
        "ENTRY_LEVEL_FRIENDLY": "👶 Entry Level"
    }
    
    display = " ".join([flag_emojis.get(f, f) for f in flags[:3]])  # Show top 3
    return display
