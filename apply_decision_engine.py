from queue_manager import ApplicationMode
from apply_extractor import detect_apply_method


def decide_application_mode(job, score):
    """
    Intelligently decide which application mode to use.
    
    Logic Flow:
    - If email exists: AUTO_APPLY (confidence >= 80%)
    - If link exists: GUIDED_APPLY (confidence 50-79%)
    - Otherwise: MANUAL_ALERT (confidence < 50%)
    
    Args:
        job: Job data dict
        score: Job match score (0-100)
    
    Returns:
        {
            "mode": ApplicationMode enum,
            "confidence_score": 0.0-1.0,
            "reasoning": "explanation string"
        }
    """
    
    # Extract apply method details
    apply_info = detect_apply_method(job)
    apply_type = apply_info.get("apply_type")
    email = apply_info.get("email")
    apply_url = apply_info.get("apply_url")
    base_confidence = apply_info.get("confidence", 0.0)
    
    # ========================================
    # 🟢 AUTO_APPLY MODE
    # ========================================
    if apply_type == "email" and email:
        # Highest confidence: email found
        confidence = 0.95
        
        return {
            "mode": ApplicationMode.AUTO_APPLY,
            "confidence_score": confidence,
            "reasoning": f"Email found: {email}. System will send auto-application.",
            "apply_email": email,
            "apply_url": None
        }
    
    # ========================================
    # 🟡 GUIDED_APPLY MODE
    # ========================================
    if apply_type == "link" and apply_url:
        # Medium confidence: apply link found
        confidence = base_confidence  # 0.75 - 0.85
        
        if confidence >= 0.5:
            return {
                "mode": ApplicationMode.GUIDED_APPLY,
                "confidence_score": confidence,
                "reasoning": f"Apply link detected with {confidence*100:.0f}% confidence. Manual steps required.",
                "apply_email": None,
                "apply_url": apply_url
            }
    
    # ========================================
    # 🔴 MANUAL_ALERT MODE (FALLBACK)
    # ========================================
    return {
        "mode": ApplicationMode.MANUAL_ALERT,
        "confidence_score": 0.0,
        "reasoning": "No clear apply method detected. Manual intervention needed.",
        "apply_email": None,
        "apply_url": job.get("link")
    }


def get_mode_emoji(mode):
    """Get emoji for application mode"""
    if mode == ApplicationMode.AUTO_APPLY:
        return "🚀"
    elif mode == ApplicationMode.GUIDED_APPLY:
        return "🟡"
    else:
        return "🔴"


def should_auto_apply(confidence_score):
    """Check if confidence meets AUTO_APPLY threshold (80%)"""
    return confidence_score >= 0.80


def should_guided_apply(confidence_score):
    """Check if confidence meets GUIDED_APPLY threshold (50-79%)"""
    return 0.50 <= confidence_score < 0.80


def should_manual_alert(confidence_score):
    """Check if confidence is below MANUAL_ALERT threshold (< 50%)"""
    return confidence_score < 0.50


def format_confidence_display(confidence_score):
    """Format confidence score for display"""
    percentage = confidence_score * 100
    
    if percentage >= 80:
        indicator = "🟢"
    elif percentage >= 50:
        indicator = "🟡"
    else:
        indicator = "🔴"
    
    return f"{indicator} Confidence: {percentage:.0f}%"
