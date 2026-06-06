from flask import Flask
import threading
import time
import hashlib
import sqlite3

from sources import collect_all_jobs
from scoring import calculate_score
from telegram_bot import send_message

app = Flask(__name__)

DB_FILE = "jobs.db"


# =========================
# DATABASE (DEDUP SYSTEM)
# =========================

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sent_jobs (
            id TEXT PRIMARY KEY
        )
    """)
    conn.commit()
    conn.close()


def is_sent(job_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM sent_jobs WHERE id=?", (job_id,))
    result = cur.fetchone()
    conn.close()
    return result is not None


def mark_sent(job_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO sent_jobs VALUES (?)", (job_id,))
    conn.commit()
    conn.close()


# =========================
# JOB ID GENERATOR
# =========================

def make_id(job):
    raw = (job.get("title", "") + job.get("link", "")).encode()
    return hashlib.md5(raw).hexdigest()


# =========================
# FORMAT MESSAGE
# =========================

def format_report(job, score):

    text = (job.get("title", "") + " " + job.get("description", "")).lower()

    if "visa" in text or "sponsorship" in text:
        visa_status = "🎫 Visa: YES"
    else:
        visa_status = "❌ Visa: Not confirmed"

    return f"""
🌍 {job.get('title')}
📍 {job.get('country')}
📊 Match Score: {score}%

{visa_status}

🔗 Apply Link:
{job.get('link')}

━━━━━━━━━━━━
"""


# =========================
# CORE ENGINE
# =========================

def run_agent():

    send_message("🚀 Job Agent Started")

    jobs = collect_all_jobs()

    print("TOTAL JOBS:", len(jobs))

    sent_count = 0
    skipped_low_score = 0

    for job in jobs:

        job_id = make_id(job)

        if is_sent(job_id):
            continue

        score = calculate_score(job)

        # 🔥 مهم: فلترة ذكية
        if score < 40:
            skipped_low_score += 1
            continue

        report = format_report(job, score)

        send_message(report)

        mark_sent(job_id)
        sent_count += 1

    send_message(
        f"✅ Completed\nSent: {sent_count}\nSkipped (low score): {skipped_low_score}"
    )


# =========================
# SCHEDULER
# =========================

def scheduler():
    while True:
        try:
            run_agent()
        except Exception as e:
            send_message(f"❌ Error: {str(e)}")

        time.sleep(86400)  # مرة يومياً


# =========================
# START THREAD
# =========================

init_db()

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
# START APP
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
