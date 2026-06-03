from flask import Flask
import requests
import os
import threading
import time
import re
from bs4 import BeautifulSoup

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
JOOBLE_API_KEY = os.getenv("JOOBLE_API_KEY", "")

# ================= TELEGRAM =================
def send(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": msg[:4000]
            },
            timeout=20
        )
    except Exception as e:
        print("Telegram Error:", e)


# ================= EMAIL EXTRACT =================
def extract_email_and_company(url):

    email = "Not provided"
    company = "Unknown"
    apply_method = "Website"

    try:
        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15
        )

        soup = BeautifulSoup(r.text, "html.parser")

        text = soup.get_text(" ")

        emails = re.findall(
            r'[\w\.-]+@[\w\.-]+\.\w+',
            text
        )

        if emails:
            email = emails[0]
            apply_method = "Email"

        title = soup.title.string if soup.title else ""
        if title:
            company = title[:60]

    except Exception as e:
        print("Parse Error:", e)

    return email, company, apply_method


# ================= FILTER =================
def is_good_job(job):

    text = (
        job["title"] +
        job["country"]
    ).lower()

    visa_words = [
        "visa",
        "sponsorship",
        "relocation",
        "training",
        "work permit",
        "language",
        "apprenticeship"
    ]

    return any(v in text for v in visa_words)


# ================= SCORE =================
def score(job):

    t = job["title"].lower()

    if any(x in t for x in [
        "nurse",
        "care",
        "health"
    ]):
        return 95

    elif any(x in t for x in [
        "admin",
        "office",
        "business"
    ]):
        return 85

    return 75


# ================= COVER LETTER =================
def cover_letter(job):

    return f"""
Dear Hiring Manager,

I am applying for the position of {job['title']}.

I hold a Diploma in Nursing and I am currently completing my Bachelor's degree in Nursing.

I have practical hospital training experience including emergency department training.

I am open to relocation, visa sponsorship and language training if required.

Please consider my application.

Sincerely,
Amjad Alsuraihi
"""


# ================= EMAIL =================
def email_text(job):

    subject = f"Application for {job['title']}"

    body = f"""
Dear Hiring Manager,

I would like to apply for the position of {job['title']}.

I hold a Diploma in Nursing and have hospital training experience.

I am willing to relocate and participate in any required training or language preparation.

Please find my CV attached.

Best regards,
Amjad Alsuraihi
"""

    return subject, body


# ================= JOB SOURCES =================
def manual_jobs():

    return [

        {
            "title":"Nursing Assistant Visa Sponsorship",
            "country":"Germany",
            "link":"https://example.com/1"
        },

        {
            "title":"Caregiver Language Training",
            "country":"UK",
            "link":"https://example.com/2"
        },

        {
            "title":"Warehouse Worker Visa Support",
            "country":"Poland",
            "link":"https://example.com/3"
        },

        {
            "title":"Hotel Worker Relocation",
            "country":"UAE",
            "link":"https://example.com/4"
        },

        {
            "title":"Farm Worker Seasonal Visa",
            "country":"Canada",
            "link":"https://example.com/5"
        }

    ]


# ================= JOOBLE =================
def jooble_jobs():

    jobs = []

    if not JOOBLE_API_KEY:
        return jobs

    try:

        url = f"https://jooble.org/api/{JOOBLE_API_KEY}"

        payload = {
            "keywords":
            "nurse OR caregiver OR nursing assistant OR admin OR warehouse OR hotel OR worker",
            "location":""
        }

        r = requests.post(url, json=payload)

        data = r.json()

        for j in data.get("jobs", []):

            jobs.append({

                "title":
                j.get("title",""),

                "country":
                j.get("location",""),

                "link":
                j.get("link","")
            })

    except Exception as e:
        print(e)

    return jobs


# ================= AGENT =================
def run_agent():

    send("🚀 Job Agent Started\nSearching global opportunities...")

    jobs = []

    jobs.extend(manual_jobs())
    jobs.extend(jooble_jobs())

    seen = set()

    for job in jobs:

        k = job["title"] + job["country"]

        if k in seen:
            continue

        seen.add(k)

        if not is_good_job(job):
            continue

        email, company, method = extract_email_and_company(
            job["link"]
        )

        subject, body = email_text(job)

        report = f"""
🌍 {job['title']}
🏢 {company}
📍 {job['country']}
📊 Match: {score(job)}%

🛂 Visa / Training:
YES

📧 Email:
{email}

📨 Apply Method:
{method}

━━━━━━━━━━

📩 Subject:
{subject}

📄 Email:
{body}

━━━━━━━━━━

📄 Cover Letter:
{cover_letter(job)}

━━━━━━━━━━

🔗 Apply:
{job['link']}
"""

        send(report)

    send("✅ Daily Report Finished")


# ================= DAILY =================
def scheduler():

    while True:

        run_agent()

        time.sleep(86400)


threading.Thread(
    target=scheduler,
    daemon=True
).start()


# ================= ROUTES =================
@app.route("/")
def home():
    return "Job Agent Running"


@app.route("/run-now")
def now():

    run_agent()

    return "done"


# ================= START =================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=10000
        )
