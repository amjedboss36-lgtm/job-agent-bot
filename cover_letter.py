import os
import openai
from queue_manager import get_cover_letter, store_cover_letter

# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")


def generate_cover_letter(job, user_profile=None):
    """
    Generate a dynamic, personalized cover letter using OpenAI.
    
    Args:
        job: Job data dict with title, company, country, description
        user_profile: Optional user profile dict with name, skills, experience
    
    Returns:
        Cover letter text (string)
    """
    
    title = job.get("title", "Position")
    description = job.get("description", "")
    country = job.get("country", "").strip()
    link = job.get("link", "")
    
    # Extract company name from description or fallback
    company = extract_company_name(description, link)
    
    # Build prompt for OpenAI
    prompt = build_cover_letter_prompt(
        job_title=title,
        company=company,
        country=country,
        job_description=description,
        user_profile=user_profile
    )
    
    try:
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional cover letter writer. Write compelling, personalized cover letters that increase application success rates. Keep it concise (3-4 paragraphs, ~200 words)."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        cover_letter = response.choices[0].message.content.strip()
        return cover_letter
        
    except Exception as e:
        print(f"OpenAI Error: {str(e)}")
        # Fallback to template if API fails
        return generate_fallback_cover_letter(title, company, country)


def build_cover_letter_prompt(job_title, company, country, job_description, user_profile=None):
    """
    Build comprehensive prompt for cover letter generation.
    """
    
    # Default profile if not provided
    if not user_profile:
        user_profile = {
            "name": "Candidate",
            "skills": "nursing, healthcare, international work",
            "experience": "Healthcare professional with international experience"
        }
    
    prompt = f"""
Generate a professional and compelling cover letter for the following job opportunity:

**Job Details:**
- Position: {job_title}
- Company: {company}
- Location: {country}
- Job Description: {job_description[:500]}...

**Candidate Profile:**
- Name: {user_profile.get('name', 'Candidate')}
- Key Skills: {user_profile.get('skills', 'Professional skills')}
- Experience: {user_profile.get('experience', 'Relevant experience')}

**Guidelines:**
1. Write in professional yet warm tone
2. Highlight enthusiasm for working in {country}
3. Address visa sponsorship interest if mentioned in job
4. Keep it concise (3-4 paragraphs, ~200 words)
5. Start with "Dear Hiring Manager," and end with "Best regards,"
6. Emphasize relevant skills and international adaptability

Generate the cover letter now:
"""
    
    return prompt


def generate_fallback_cover_letter(job_title, company, country):
    """
    Fallback template if OpenAI API fails.
    """
    return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company}. With my professional background and enthusiasm for international opportunities in {country}, I am confident in my ability to contribute meaningfully to your team.

Throughout my career, I have developed expertise in delivering high-quality service in diverse environments. I am particularly attracted to this opportunity as it aligns with my career goals and my commitment to professional growth in international settings.

I am excited about the possibility of joining your organization and bringing my skills, dedication, and adaptability to support your team's success.

Best regards,
Candidate"""


def extract_company_name(description, link):
    """
    Extract company name from job description or URL.
    """
    # Try to extract from description first (look for "at" pattern)
    if "at " in description.lower():
        parts = description.lower().split("at ")
        if len(parts) > 1:
            company = parts[1].split(" ")[0].strip()
            if company and len(company) > 2:
                return company.title()
    
    # Extract from URL domain
    try:
        from urllib.parse import urlparse
        domain = urlparse(link).netloc
        company = domain.replace("www.", "").split(".")[0].title()
        return company
    except:
        return "Our Company"


def cover_letter_exists(job_id):
    """Check if cover letter already generated"""
    return get_cover_letter(job_id) is not None


def get_or_generate_cover_letter(job_id, job, user_profile=None):
    """
    Get existing cover letter from cache or generate new one.
    """
    
    # Check if already cached
    existing = get_cover_letter(job_id)
    if existing:
        return existing
    
    # Generate new
    cover_letter = generate_cover_letter(job, user_profile)
    
    # Store in database
    store_cover_letter(job_id, cover_letter)
    
    return cover_letter


def format_cover_letter_for_display(cover_letter, max_length=300):
    """
    Format cover letter for Telegram display (truncate if needed).
    """
    if len(cover_letter) <= max_length:
        return cover_letter
    
    return cover_letter[:max_length] + "...\n\n[Full letter in database]"
