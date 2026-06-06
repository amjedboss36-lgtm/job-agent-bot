import sqlite3
import os
from datetime import datetime, timedelta
from enum import Enum

DB_FILE = os.getenv("DB_FILE", "jobs.db")


class ApplicationMode(Enum):
    AUTO_APPLY = "AUTO_APPLY"
    GUIDED_APPLY = "GUIDED_APPLY"
    MANUAL_ALERT = "MANUAL_ALERT"


class JobStatus(Enum):
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


def init_db():
    """Initialize SQLite database with enhanced schema"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Main jobs table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            link TEXT NOT NULL,
            country TEXT,
            description TEXT,
            source TEXT,
            score INTEGER,
            priority_flags TEXT,
            apply_mode TEXT,
            apply_email TEXT,
            apply_url TEXT,
            confidence_score REAL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_at TIMESTAMP,
            failed_reason TEXT
        )
    """)

    # Sent jobs tracking (dedup)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sent_jobs (
            job_id TEXT PRIMARY KEY,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    """)

    # Cover letters cache
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cover_letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL UNIQUE,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    """)

    # Rate limiting log
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rate_limit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_count INTEGER
        )
    """)

    conn.commit()
    conn.close()


def job_exists(job_id):
    """Check if job already in queue"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM jobs WHERE id=?", (job_id,))
    result = cur.fetchone()
    conn.close()
    return result is not None


def add_job(job_data):
    """Add job to queue"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO jobs 
            (id, title, link, country, description, source, score, 
             priority_flags, apply_mode, apply_email, apply_url, 
             confidence_score, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_data.get("id"),
            job_data.get("title"),
            job_data.get("link"),
            job_data.get("country"),
            job_data.get("description"),
            job_data.get("source"),
            job_data.get("score"),
            job_data.get("priority_flags", ""),
            job_data.get("apply_mode", ApplicationMode.MANUAL_ALERT.value),
            job_data.get("apply_email", ""),
            job_data.get("apply_url", ""),
            job_data.get("confidence_score", 0.0),
            JobStatus.PENDING.value
        ))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def get_pending_jobs(limit=None):
    """Get pending jobs ordered by: score DESC, created_at ASC"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    query = """
        SELECT * FROM jobs 
        WHERE status = ? 
        ORDER BY score DESC, created_at ASC
    """
    params = [JobStatus.PENDING.value]

    if limit:
        query += " LIMIT ?"
        params.append(limit)

    cur.execute(query, params)
    jobs = cur.fetchall()
    conn.close()

    return jobs


def get_jobs_by_mode(mode):
    """Get jobs by application mode"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM jobs 
        WHERE apply_mode = ? AND status = ?
        ORDER BY score DESC
    """, (mode, JobStatus.PENDING.value))
    jobs = cur.fetchall()
    conn.close()
    return jobs


def update_job_status(job_id, status, failed_reason=None):
    """Update job status"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    if status == JobStatus.SENT.value:
        cur.execute("""
            UPDATE jobs SET status = ?, sent_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (status, job_id))
    else:
        cur.execute("""
            UPDATE jobs SET status = ?, failed_reason = ? 
            WHERE id = ?
        """, (status, failed_reason, job_id))

    conn.commit()
    conn.close()


def mark_sent(job_id):
    """Mark job as sent (dedup)"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO sent_jobs (job_id) VALUES (?)", (job_id,))
    conn.commit()
    conn.close()


def get_today_sent_count():
    """Get count of jobs sent TODAY (rate limiting)"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    today = datetime.now().date()
    cur.execute("""
        SELECT COUNT(*) FROM jobs 
        WHERE status = ? AND DATE(sent_at) = ?
    """, (JobStatus.SENT.value, today))

    count = cur.fetchone()[0]
    conn.close()
    return count


def can_send_today(max_per_day=10):
    """Check if we can send more jobs today (rate limit)"""
    sent_today = get_today_sent_count()
    return sent_today < max_per_day


def store_cover_letter(job_id, content):
    """Store generated cover letter"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO cover_letters (job_id, content)
            VALUES (?, ?)
        """, (job_id, content))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def get_cover_letter(job_id):
    """Retrieve cover letter for job"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT content FROM cover_letters WHERE job_id = ?", (job_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else None


def cleanup_old_jobs(days=30):
    """Remove old completed jobs (archival)"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cutoff_date = datetime.now() - timedelta(days=days)

    cur.execute("""
        DELETE FROM jobs 
        WHERE status IN (?, ?) AND sent_at < ?
    """, (JobStatus.SENT.value, JobStatus.FAILED.value, cutoff_date))

    conn.commit()
    conn.close()
