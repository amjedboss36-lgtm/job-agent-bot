from flask import Flask
import requests
import os
import threading
import time
import re
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

app = Flask(__name__)

# ================= ENV =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
JOOBLE_API_KEY = os.getenv("JOOBLE_API_KEY", "")

SENT_FILE = "sent_jobs.txt"

# ================= TELEGRAM =================
def send(msg):
    if not BOT_TOKEN or not CHAT_ID:
        print("Missing Telegram ENV")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": msg[:4000]
        }, timeout=20)
    except Exception as e:
        print("Telegram Error:", e)

# ================= SENT JOBS =================
def load_sent():
    try:
        with open(SENT_FILE, "r") as f:
            return set(f.read().splitlines())
    except:
        return set()

def save_sent(job_id):
    with open(SENT_FILE, "a") as f:
        f.write(job_id + "\n")

# ================= CLEAN TEXT =================
def clean(t):
    return re.sub(r"\s+", " ", t or "").strip()

# ================= FILTER =================
def is_good_job(text):
    text = text.lower()

    keywords = [
        "visa", "sponsorship", "relocation", "work permit",
        "training", "language", "international",
        "nurse", "nursing", "care", "caregiver",
        "assistant", "hospital", "health",
        "warehouse", "hotel", "worker", "admin", "business"
    ]

    return any(k in text for k in keywords)

# ================= SCORE =================
def score(title):
    t = title.lower()

    if any(x in t for x in ["nurse", "care", "hospital", "caregiver"]):
        return 95
    if any(x in t for x in ["admin", "office", "business"]):
        return 85
    return 75

# ================= COVER LETTER =================
def cover_letter(job):
    return f"""
Dear Hiring Manager,

I am applying for {job['title']}.

I am a Diploma Nursing graduate and currently completing my Bachelor's degree in Nursing.

I have clinical training experience in hospitals including emergency department training.

I am open to relocation, visa sponsorship, and language training.

Sincerely,
Amjad Alsuraihi
"""

# ================= EMAIL =================
def email_text(job):
    subject = f"Application for {job['title']}"

    body = f"""
Dear Hiring Manager,

I would like to apply for {job['title']}.

I am a nursing graduate with hospital training experience.

I am open to relocation and sponsorship opportunities.

Best regards,
Amjad
"""

    return subject, body

# ================= EXTRACT EMAIL =================
def extract_email(url):
    email = "Not found"
    company = "Unknown"
    method = "Website"

    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        text = soup.get_text(" ")
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)

        if emails:
            email = emails[0]
            method = "Email"

        if soup.title:
            company = clean(soup.title.text)[:80]

    except:
        pass

    return email, company, method

# ================= SOURCES =================
def eures_jobs():
    return [{
        "title": "EURES Nursing / Healthcare Opportunities",
        "country": "Europe",
        "link": "https://eures.europa.eu"
    }]

def indeed_jobs():
    jobs = []

    feeds = [
        "nursing assistant visa sponsorship",
        "caregiver sponsorship",
        "warehouse worker visa",
        "hotel worker relocation"
    ]

    for q in feeds:
        try:
            url = "https://rss.indeed.com/rss?q=" + q.replace(" ", "+")
            r = requests.get(url, timeout=20)

            root = ET.fromstring(r.text)

            for item in root.findall(".//item")[:5]:
                jobs.append({
                    "title": clean(item.findtext("title")),
                    "country": "Indeed",
                    "link": clean(item.findtext("link"))
                })
        except:
            pass

    return jobs

def jooble_jobs():
    jobs = []

    if not JOOBLE_API_KEY:
        return jobs

    try:
        url = f"https://jooble.org/api/{JOOBLE_API_KEY}"
        payload = {
            "keywords": "nurse caregiver nursing assistant admin hotel warehouse worker",
            "location": ""
        }

        r = requests.post(url, json=payload, timeout=20)
        data = r.json()

        for j in data.get("jobs", [])[:10]:
            jobs.append({
                "title": clean(j.get("title")),
                "country": clean(j.get("location")),
                "link": clean(j.get("link"))
            })
    except:
        pass

    return jobs

# ================= AGENT =================
def run_agent():
    send("🚀 Daily Job Agent Started")

    jobs = []
    jobs += eures_jobs()
    jobs += indeed_jobs()
    jobs += jooble_jobs()

    sent = load_sent()

    for job in jobs:
        key = job["title"] + job["link"]

        if key in sent:
            continue

        if not is_good_job(job["title"]):
            continue

        save_sent(key)

        email, company, method = extract_email(job["link"])
        subject, body = email_text(job)

        report = f"""
🌍 {job['title']}
🏢 {company}
📍 {job['country']}
📊 Match: {score(job['title'])}%

🛂 Visa/Relocation/Training: Possible

📧 Email: {email}
📨 Method: {method}

━━━━━━━━━━
📩 Subject:
{subject}

📄 Email:
{body}

━━━━━━━━━━
📄 Cover Letter:
{cover_letter(job)}

━━━━━━━━━━
🔗 Link:
{job['link']}
"""

        send(report)

    send("✅ Daily Report Completed")

# ================= SCHEDULER =================
def scheduler():
    while True:
        try:
            run_agent()
        except Exception as e:
            send(f"Error: {e}")

        time.sleep(86400)

threading.Thread(target=scheduler, daemon=True).start()

# ================= ROUTES =================
@app.route("/")
def home():
    return "Job Agent Running"

@app.route("/run-now")
def run_now():
    run_agent()
    return "Triggered"

# ================= START =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
