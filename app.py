from flask import Flask
import requests
import os
import threading
import time

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
JOOBLE_API_KEY = os.getenv("JOOBLE_API_KEY", "")


# ================= TELEGRAM =================
def send(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print("Telegram Error:", e)


# ================= JOB FILTER =================
def is_good_job(job):
    text = (job["title"] + job["country"]).lower()

    keywords = [
        "visa",
        "sponsorship",
        "training",
        "relocation",
        "no language",
        "work permit",
        "apprenticeship"
    ]

    return any(k in text for k in keywords)


# ================= COVER LETTER =================
def cover_letter(job):
    return f"""
Dear Hiring Manager,

I am applying for the position of {job['title']}.

I hold a Diploma in Nursing and I am currently completing my Bachelor's degree in Nursing.
I also have hospital training experience in emergency and general wards.

I am open to relocation, visa sponsorship, and any required training or language programs.

Kindly consider my application.

Sincerely,
Amjad
"""


# ================= EMAIL =================
def email_text(job):
    subject = f"Application for {job['title']} Position"

    body = f"""
Dear Hiring Manager,

I would like to apply for the position of {job['title']}.

I have a Diploma in Nursing and practical hospital training experience.

I am open to relocation and visa sponsorship opportunities.

Please consider my application.

Best regards,
Amjad
"""

    return subject, body


# ================= SCORE =================
def score(job):
    title = job["title"].lower()

    if "nurse" in title or "care" in title:
        return 95
    elif "warehouse" in title or "factory" in title:
        return 80
    else:
        return 75


# ================= JOB SOURCES =================
def get_manual_jobs():
    return [
        {"title": "Nursing Assistant Visa Sponsorship", "country": "Germany", "link": "https://example.com/1"},
        {"title": "Caregiver No Language Required", "country": "UK", "link": "https://example.com/2"},
        {"title": "Warehouse Worker Training Visa", "country": "Poland", "link": "https://example.com/3"},
        {"title": "Hotel Staff Visa Sponsorship", "country": "UAE", "link": "https://example.com/4"},
        {"title": "Farm Worker Seasonal Visa", "country": "Canada", "link": "https://example.com/5"},
        {"title": "Factory Worker Work Permit", "country": "Romania", "link": "https://example.com/6"},
        {"title": "Office Assistant Visa Support", "country": "UK", "link": "https://example.com/7"}
    ]


def get_jooble_jobs():
    jobs = []

    if not JOOBLE_API_KEY:
        return jobs

    try:
        url = f"https://jooble.org/api/{JOOBLE_API_KEY}"
        payload = {
            "keywords": "nurse OR assistant OR warehouse OR hotel OR factory",
            "location": "worldwide"
        }

        res = requests.post(url, json=payload)
        data = res.json()

        for j in data.get("jobs", []):
            jobs.append({
                "title": j.get("title", ""),
                "country": j.get("location", ""),
                "link": j.get("link", "")
            })

    except Exception as e:
        print("Jooble error:", e)

    return jobs


# ================= AGENT =================
def run_agent():
    send("🚀 Daily Job Agent Started... Searching global opportunities 🌍")

    jobs = []
    jobs.extend(get_manual_jobs())
    jobs.extend(get_jooble_jobs())

    seen = set()

    for job in jobs:

        key = job["title"] + job["country"]
        if key in seen:
            continue
        seen.add(key)

        if not is_good_job(job):
            continue

        subject, email = email_text(job)

        msg = f"""
🌍 {job['title']}
📍 {job['country']}
📊 Match: {score(job)}%

🛂 Visa / Training: YES

🔗 Apply Link:
{job['link']}

━━━━━━━━━━━━━━━
📩 EMAIL SUBJECT:
{subject}

📄 EMAIL BODY:
{email}

━━━━━━━━━━━━━━━
📄 COVER LETTER:
{cover_letter(job)}
"""

        send(msg)

    send("✅ Daily Job Report Completed")


# ================= SCHEDULER =================
def scheduler():
    while True:
        run_agent()
        time.sleep(86400)  # 24 hours


threading.Thread(target=scheduler, daemon=True).start()


# ================= ROUTES =================
@app.route("/")
def home():
    return "Job Agent Running 24/7 🚀"


@app.route("/run-now")
def run_now():
    run_agent()
    return "Manual run completed"


# ================= START =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
