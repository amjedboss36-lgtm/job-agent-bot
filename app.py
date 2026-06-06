from flask import Flask
import threading
import time
import hashlib

from sources import collect_all_jobs
from filters import is_valid_job_link
from scoring import calculate_score
from telegram_bot import send_message

app = Flask(__name__)

SENT_FILE = "sent_jobs.txt"


# =========================
# SENT SYSTEM (HASH BASED)
# =========================

def load_sent():
    try:
        with open(SENT_FILE, "r") as f:
            return set(f.read().splitlines())
    except:
        return set()


def save_sent(job_id):
    with open(SENT_FILE, "a") as f:
        f.write(job_id + "\n")


def make_id(job):
    raw = (job.get("title", "") + job.get("link", "")).encode()
    return hashlib.md5(raw).hexdigest()


# =========================
# REPORT FORMAT
# =========================

def format_report(job, score):

    benefits = job.get("benefits", {})

    return f"""
🌍 {job.get('title')}
📍 {job.get('country')}
📊 Match Score: {score}%

💼 Visa: {benefits.get('visa', False)}
📦 Relocation: {benefits.get('relocation', False)}

🔗 Apply Link:
{job.get('link')}

━━━━━━━━━━━━
"""

# =========================
# AGENT CORE
# =========================

def run_agent():
    send_message("🚀 Job Agent Started")

    jobs = collect_all_jobs()
    print("JOBS FOUND:", len(jobs))
    sent = load_sent()

    for job in jobs:

        job_id = make_id(job)

        if job_id in sent:
            continue

        # VALIDATE LINK
        if not is_valid_job_link(job.get("link")):
            continue

        score = calculate_score(job)

        report = format_report(job, score)

        print("Sending:", job.get("title"))
send_message(report)

        save_sent(job_id)

    send_message("✅ Job Agent Completed")


# =========================
# SCHEDULER
# =========================

def scheduler():
    while True:
        try:
            run_agent()
        except Exception as e:
            send_message(f"❌ Error: {e}")

        time.sleep(86400)


threading.Thread(target=scheduler, daemon=True).start()


# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    return "Job Agent Running"


@app.route("/run-now")
def run_now():
    run_agent()
    return "Triggered"


# =========================
# START
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
