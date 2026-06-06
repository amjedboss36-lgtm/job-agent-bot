import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from scraper import scrape_jobs
from scoring import calculate_score
from apply_decision_engine import decide_application_mode
from cover_letter import get_or_generate_cover_letter
from queue_manager import (
    init_db, add_job, get_pending_jobs, 
    update_job_status, mark_sent, can_send_today,
    ApplicationMode, JobStatus
)
from telegram_bot import notify_job_sent, notify_error, notify_summary, send_email_application

# Load environment
load_dotenv()

app = Flask(__name__)

# Initialize database on startup
init_db()


def safe_extract_score(score_result):
    """
    Safely extract score from calculate_score() result.
    Handles both dict and int types.
    
    Args:
        score_result: dict with {"score": int, "priority_flags": list} or int
    
    Returns:
        tuple: (score: int, flags: list)
    """
    try:
        # If it's already a dict with expected structure
        if isinstance(score_result, dict):
            score = score_result.get("score", 0)
            flags = score_result.get("priority_flags", [])
            
            # Ensure score is int
            if not isinstance(score, int):
                score = int(score) if isinstance(score, (str, float)) else 0
            
            # Ensure flags is list
            if not isinstance(flags, list):
                flags = []
            
            return score, flags
        
        # If it's just an int (legacy format)
        elif isinstance(score_result, int):
            return score_result, []
        
        # Default fallback
        else:
            return 0, []
    
    except Exception as e:
        print(f"⚠️ Error extracting score: {e}")
        return 0, []


def safe_compare_score(score, threshold=50):
    """
    Safely compare score with threshold.
    
    Args:
        score: Score value (should be int)
        threshold: Comparison threshold (default 50)
    
    Returns:
        bool: True if score >= threshold, False otherwise
    """
    try:
        if not isinstance(score, int):
            if isinstance(score, (str, float)):
                score = int(score)
            else:
                return False
        
        return score >= threshold
    except (TypeError, ValueError) as e:
        print(f"⚠️ Error comparing score: {e}")
        return False


@app.route("/scrape", methods=["POST"])
def scrape_jobs_route():
    """
    Scrape jobs from configured sources and add to queue.
    """
    try:
        print("🔍 Starting job scraping...")
        
        # Scrape jobs
        jobs = scrape_jobs()
        print(f"✅ Scraped {len(jobs)} jobs")
        
        added_count = 0
        skipped_count = 0
        error_count = 0
        
        # Process each job
        for job in jobs:
            try:
                # Calculate score - safely extract score and flags
                score_result = calculate_score(job)
                score, flags = safe_extract_score(score_result)
                
                # Ensure job fields are set correctly
                job["score"] = score
                job["priority_flags"] = flags
                
                # Add to queue if score is good enough
                if safe_compare_score(score, threshold=50):
                    success = add_job(job)
                    if success:
                        added_count += 1
                        print(f"✅ Added: {job.get('title')} (score: {score})")
                    else:
                        error_count += 1
                else:
                    skipped_count += 1
                    print(f"⏭️ Skipped (low score: {score}): {job.get('title')}")
            
            except Exception as e:
                print(f"⚠️ Error processing job: {str(e)}")
                error_count += 1
                continue
        
        return jsonify({
            "status": "success",
            "scraped": len(jobs),
            "added": added_count,
            "skipped": skipped_count,
            "errors": error_count
        })
        
    except Exception as e:
        error_msg = f"Scraping error: {str(e)}"
        print(f"❌ {error_msg}")
        notify_error(error_msg)
        return jsonify({"status": "error", "message": error_msg}), 500


@app.route("/process", methods=["POST"])
def process_jobs_route():
    """
    Process pending jobs and execute applications.
    """
    try:
        print("⚙️ Processing pending jobs...")
        
        # Check rate limit
        if not can_send_today(max_per_day=10):
            return jsonify({
                "status": "rate_limited",
                "message": "Daily limit reached (10 applications/day)"
            }), 429
        
        # Get pending jobs
        pending = get_pending_jobs(limit=5)
        print(f"📋 Found {len(pending)} pending jobs")
        
        sent_count = 0
        failed_count = 0
        skipped_count = 0
        user_profile = {
            "name": os.getenv("USER_NAME", "Candidate"),
            "skills": os.getenv("USER_SKILLS", "healthcare, nursing"),
            "experience": os.getenv("USER_EXPERIENCE", "Professional with international experience")
        }
        
        # Process each job
        for job_row in pending:
            job_id = None
            
            try:
                # Safely construct job dict from database row
                job_id = job_row[0]
                
                # Safely extract and validate score from database
                db_score = job_row[6]
                if isinstance(db_score, dict):
                    db_score = db_score.get("score", 0)
                
                # Ensure score is int
                if not isinstance(db_score, int):
                    if isinstance(db_score, (str, float)):
                        db_score = int(db_score)
                    else:
                        db_score = 0
                
                # Safely extract flags
                db_flags = job_row[7]
                if isinstance(db_flags, str):
                    db_flags = db_flags.split(",") if db_flags else []
                elif not isinstance(db_flags, list):
                    db_flags = []
                
                # Construct job dict with validated types
                job = {
                    "id": job_row[0],
                    "title": str(job_row[1]) if job_row[1] else "Unknown",
                    "link": str(job_row[2]) if job_row[2] else "",
                    "country": str(job_row[3]) if job_row[3] else "Unknown",
                    "description": str(job_row[4]) if job_row[4] else "",
                    "source": str(job_row[5]) if job_row[5] else "Unknown",
                    "score": db_score,
                    "priority_flags": db_flags
                }
                
                print(f"📌 Processing job: {job['title']} (ID: {job_id}, Score: {job['score']})")
                
                # Decide application mode
                decision = decide_application_mode(job, job["score"])
                
                # Handle AUTO_APPLY
                if decision["mode"] == ApplicationMode.AUTO_APPLY:
                    print(f"🚀 AUTO_APPLY: {job['title']}")
                    
                    try:
                        # Generate cover letter
                        cover_letter = get_or_generate_cover_letter(job_id, job, user_profile)
                        
                        # Send email
                        email_success = send_email_application(
                            to_email=decision["apply_email"],
                            job_title=job["title"],
                            cover_letter=cover_letter
                        )
                        
                        if email_success:
                            update_job_status(job_id, JobStatus.SENT.value)
                            mark_sent(job_id)
                            sent_count += 1
                            print(f"✅ Email sent successfully for: {job['title']}")
                        else:
                            update_job_status(job_id, JobStatus.FAILED.value, "Email sending failed")
                            failed_count += 1
                            print(f"❌ Email sending failed for: {job['title']}")
                    
                    except Exception as email_error:
                        error_msg = f"Email processing error: {str(email_error)}"
                        print(f"❌ {error_msg}")
                        update_job_status(job_id, JobStatus.FAILED.value, error_msg)
                        failed_count += 1
                
                # Handle GUIDED_APPLY (manual steps required)
                elif decision["mode"] == ApplicationMode.GUIDED_APPLY:
                    print(f"🟡 GUIDED_APPLY: {job['title']}")
                    update_job_status(job_id, JobStatus.QUEUED.value)
                    skipped_count += 1
                
                # Handle MANUAL_ALERT (user action needed)
                else:
                    print(f"🔴 MANUAL_ALERT: {job['title']}")
                    update_job_status(job_id, JobStatus.QUEUED.value)
                    skipped_count += 1
                
                # Send Telegram notification
                notify_job_sent(job, decision, success=True)
                
            except Exception as e:
                error_msg = f"Job processing error: {str(e)}"
                print(f"❌ {error_msg}")
                if job_id:
                    update_job_status(job_id, JobStatus.FAILED.value, error_msg)
                    failed_count += 1
                notify_error(f"Failed to process job {job_id}: {error_msg}")
        
        # Send summary
        notify_summary(sent_count, skipped_count, failed_count)
        
        return jsonify({
            "status": "success",
            "processed": len(pending),
            "sent": sent_count,
            "guided": skipped_count,
            "failed": failed_count
        })
        
    except Exception as e:
        error_msg = f"Processing error: {str(e)}"
        print(f"❌ {error_msg}")
        notify_error(error_msg)
        return jsonify({"status": "error", "message": error_msg}), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "job-agent-bot"}), 200


@app.route("/stats", methods=["GET"])
def stats():
    """Get job queue statistics"""
    try:
        all_pending = get_pending_jobs()
        return jsonify({
            "pending_jobs": len(all_pending),
            "daily_limit": 10,
            "can_send_today": can_send_today(max_per_day=10)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
