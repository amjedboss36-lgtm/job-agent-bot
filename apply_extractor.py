import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

# ✅ TRUSTED APPLY DOMAINS (WHITELIST)
TRUSTED_APPLY_DOMAINS = {
    "linkedin.com",
    "indeed.com",
    "greenhouse.io",
    "lever.co",
    "workable.com",
    "talentdesk.io",
    "smartrecruiters.com",
    "taleo.net",
    "bamboohr.com",
    "ziprecruiter.com",
    "monster.com",
    "glassdoor.com",
    "careerbuilder.com",
    "jobvite.com",
    "recruitee.com",
    "honeypot.io",
    "remoteok.com",
    "angel.co",
    "producthunt.com",
    "jobs.github.com",
    "stack-overflow.com",
    "seek.com.au",
    "arbeitnow.com"
}

# ❌ BLOCKED APPLY DOMAINS
BLOCKED_DOMAINS = {
    "eures.europa.eu",
    "facebook.com",
    "twitter.com",
    "instagram.com",
    "tiktok.com"
}


def extract_email_from_text(text):
    """
    Extract email address from text.
    Returns first valid email found.
    """
    if not text:
        return None

    # Email regex pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, text)

    # Filter out common fake/test emails
    fake_emails = ["test@", "example@", "no-reply@", "noreply@"]
    
    for email in matches:
        if not any(fake in email.lower() for fake in fake_emails):
            return email

    return None


def extract_urls_from_html(html_content):
    """
    Extract all URLs from HTML content.
    Returns list of URLs found in href attributes.
    """
    if not html_content:
        return []

    try:
        soup = BeautifulSoup(html_content, 'lxml')
        urls = []

        for link in soup.find_all('a', href=True):
            url = link.get('href', '').strip()
            if url and url.startswith('http'):
                urls.append(url)

        return list(set(urls))  # Deduplicate
    except:
        return []


def sanitize_url(url):
    """
    Remove tracking parameters from URL.
    Cleans: ?utm_source, ?ref, ?utm_*, etc.
    """
    if not url:
        return None

    try:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)

        # Remove tracking parameters
        tracking_keys = [k for k in query_params.keys() if 'utm_' in k or k == 'ref']
        
        for key in tracking_keys:
            del query_params[key]

        # Rebuild URL without tracking params
        clean_query = '&'.join(f"{k}={v[0]}" for k, v in query_params.items())
        
        if clean_query:
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{clean_query}"
        else:
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        return clean_url
    except:
        return url


def is_trusted_domain(url):
    """
    Check if URL domain is in whitelist.
    Returns True if trusted, False otherwise.
    """
    if not url:
        return False

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace('www.', '')

        # Check blocklist first
        for blocked in BLOCKED_DOMAINS:
            if blocked in domain:
                return False

        # Check whitelist
        for trusted in TRUSTED_APPLY_DOMAINS:
            if trusted in domain:
                return True

        return False
    except:
        return False


def find_apply_url_in_description(description):
    """
    Search for apply link in job description.
    Prioritizes trusted domains.
    Returns first trusted apply link or None.
    """
    if not description:
        return None

    urls = extract_urls_from_html(description)

    # Prioritize trusted domains
    for url in urls:
        if is_trusted_domain(url):
            return sanitize_url(url)

    return None


def detect_apply_method(job):
    """
    Main function: Detect how to apply to job.
    
    Returns:
    {
        "apply_type": "email|link|form|unknown",
        "email": "contact@company.com or None",
        "apply_url": "https://job.link or None",
        "confidence": 0.0-1.0
    }
    """
    result = {
        "apply_type": "unknown",
        "email": None,
        "apply_url": None,
        "confidence": 0.0
    }

    title = job.get("title", "")
    description = job.get("description", "")
    link = job.get("link", "")

    # ==================
    # 1️⃣ EMAIL DETECTION
    # ==================
    email = extract_email_from_text(description)
    
    if email:
        result["apply_type"] = "email"
        result["email"] = email
        result["confidence"] = 0.95
        return result

    # ==================
    # 2️⃣ LINK DETECTION
    # ==================
    apply_url = find_apply_url_in_description(description)
    
    if apply_url and apply_url != link:
        result["apply_type"] = "link"
        result["apply_url"] = apply_url
        result["confidence"] = 0.85
        return result

    # Check if main link is trusted for direct apply
    if link and is_trusted_domain(link):
        result["apply_type"] = "link"
        result["apply_url"] = link
        result["confidence"] = 0.75
        return result

    # ==================
    # 3️⃣ FALLBACK
    # ==================
    result["apply_type"] = "unknown"
    result["confidence"] = 0.0
    
    return result
