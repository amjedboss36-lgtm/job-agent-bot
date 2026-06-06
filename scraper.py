import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Job scraping sources
SOURCES = {
    "linkedin": "https://www.linkedin.com/jobs/search/?keywords=nurse",
    "indeed": "https://www.indeed.com/jobs?q=nurse",
    "greenhouse": "https://greenhouse.io/",
    "lever": "https://lever.co/",
}


def scrape_jobs():
    """
    Scrape jobs from multiple sources.
    Returns: List of job dicts with title, link, country, description
    """
    
    all_jobs = []
    
    try:
        # Try to scrape from Indeed (most reliable)
        indeed_jobs = scrape_indeed()
        all_jobs.extend(indeed_jobs)
        print(f"✅ Indeed: {len(indeed_jobs)} jobs")
    except Exception as e:
        print(f"❌ Indeed scrape failed: {e}")
    
    try:
        # Try to scrape from LinkedIn
        linkedin_jobs = scrape_linkedin()
        all_jobs.extend(linkedin_jobs)
        print(f"✅ LinkedIn: {len(linkedin_jobs)} jobs")
    except Exception as e:
        print(f"❌ LinkedIn scrape failed: {e}")
    
    try:
        # Try to scrape from Greenhouse
        greenhouse_jobs = scrape_greenhouse()
        all_jobs.extend(greenhouse_jobs)
        print(f"✅ Greenhouse: {len(greenhouse_jobs)} jobs")
    except Exception as e:
        print(f"❌ Greenhouse scrape failed: {e}")
    
    return all_jobs


def scrape_indeed():
    """Scrape jobs from Indeed"""
    jobs = []
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        url = "https://www.indeed.com/jobs?q=nurse+visa+sponsorship"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find job cards
        job_cards = soup.find_all('div', class_='job_seen_beacon')
        
        for card in job_cards[:20]:  # Limit to 20 jobs
            try:
                # Extract job details
                title_elem = card.find('h2', class_='jobTitle')
                link_elem = card.find('a')
                company_elem = card.find('span', class_='companyName')
                location_elem = card.find('div', class_='companyLocation')
                
                if not all([title_elem, link_elem, company_elem]):
                    continue
                
                title = title_elem.get_text(strip=True)
                link = link_elem.get('href', '')
                company = company_elem.get_text(strip=True)
                location = location_elem.get_text(strip=True) if location_elem else "Unknown"
                
                # Make absolute URL
                if link.startswith('/'):
                    link = urljoin('https://indeed.com', link)
                
                job = {
                    "title": title,
                    "link": link,
                    "country": extract_country(location),
                    "description": f"{title} at {company}",
                    "source": "Indeed"
                }
                
                jobs.append(job)
            except Exception as e:
                print(f"Error parsing Indeed job: {e}")
                continue
    
    except Exception as e:
        print(f"Indeed scraping error: {e}")
    
    return jobs


def scrape_linkedin():
    """Scrape jobs from LinkedIn"""
    jobs = []
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        # LinkedIn requires authentication, using simplified approach
        url = "https://www.linkedin.com/jobs/search/?keywords=nurse&f_V=1"  # f_V=1 means visa sponsorship
        response = requests.get(url, headers=headers, timeout=10)
        
        # LinkedIn heavily uses JavaScript, so basic scraping may not work
        # This is a placeholder for future enhancement
        jobs = []
    
    except Exception as e:
        print(f"LinkedIn scraping error: {e}")
    
    return jobs


def scrape_greenhouse():
    """Scrape jobs from Greenhouse job boards"""
    jobs = []
    
    try:
        # Greenhouse boards for various companies
        greenhouse_boards = [
            "https://boards.greenhouse.io/",
            "https://jobs.greenhouse.io/"
        ]
        
        for base_url in greenhouse_boards:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                
                response = requests.get(base_url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for job links (structure varies by board)
                job_links = soup.find_all('a', class_='job-title')
                
                for link in job_links[:15]:
                    try:
                        title = link.get_text(strip=True)
                        job_url = link.get('href', '')
                        
                        if not job_url.startswith('http'):
                            job_url = urljoin(base_url, job_url)
                        
                        job = {
                            "title": title,
                            "link": job_url,
                            "country": "Unknown",
                            "description": title,
                            "source": "Greenhouse"
                        }
                        
                        jobs.append(job)
                    except Exception as e:
                        continue
            
            except Exception as e:
                continue
    
    except Exception as e:
        print(f"Greenhouse scraping error: {e}")
    
    return jobs


def extract_country(location_str):
    """Extract country from location string"""
    if not location_str:
        return "Unknown"
    
    location_lower = location_str.lower()
    
    # Common country mappings
    countries = {
        "germany": ["berlin", "hamburg", "munich", "cologne", "frankfurt"],
        "netherlands": ["amsterdam", "rotterdam", "rotterdam", "utrecht", "groningen"],
        "uk": ["london", "manchester", "birmingham", "leeds", "glasgow"],
        "canada": ["toronto", "vancouver", "calgary", "ottawa", "montreal"],
        "australia": ["sydney", "melbourne", "brisbane", "perth", "adelaide"],
        "usa": ["new york", "los angeles", "chicago", "houston", "miami"],
        "sweden": ["stockholm", "gothenburg", "malmo"],
        "norway": ["oslo", "bergen", "trondheim"],
        "france": ["paris", "lyon", "marseille", "toulouse"],
        "spain": ["madrid", "barcelona", "valencia", "seville"],
    }
    
    for country, cities in countries.items():
        if any(city in location_lower for city in cities):
            return country.title()
    
    # If country name itself is in location
    if "germany" in location_lower:
        return "Germany"
    elif "netherlands" in location_lower or "holland" in location_lower:
        return "Netherlands"
    elif "united kingdom" in location_lower or "uk" in location_lower:
        return "UK"
    elif "canada" in location_lower:
        return "Canada"
    elif "australia" in location_lower:
        return "Australia"
    elif "usa" in location_lower or "united states" in location_lower:
        return "USA"
    elif "sweden" in location_lower:
        return "Sweden"
    elif "norway" in location_lower:
        return "Norway"
    elif "france" in location_lower:
        return "France"
    elif "spain" in location_lower:
        return "Spain"
    elif "remote" in location_lower:
        return "Remote"
    else:
        return location_str.split(',')[-1].strip() if ',' in location_str else location_str


def validate_job(job):
    """Validate job data structure"""
    required_fields = ["title", "link", "country", "description", "source"]
    return all(field in job and job[field] for field in required_fields)
