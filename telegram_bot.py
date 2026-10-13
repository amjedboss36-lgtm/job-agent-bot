import os
import requests
import smtplib
import os
import re
import mimetypes
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apply_decision_engine import format_confidence_display, get_mode_emoji
from scoring import format_flags_display
from queue_manager import ApplicationMode

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


def send_message(message: str):
    """Send message to Telegram"""
    if not BOT_TOKEN or not CHAT_ID:
        print("Missing BOT_TOKEN or CHAT_ID")
        return False

    # Distinguish international alerts from the Yemen nursing project in the shared chat.
    if not message.startswith("[وظائف عالمية]"):
        message = "[وظائف عالمية]\\n\\n" + message
    # The same Telegram chat is shared with the Yemen nursing project.
    if not message.startswith("[وظائف عالمية]"):
        message = "[وظائف عالمية]\\n\\n" + message
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:
        response = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": message[:4000],
                "parse_mode": "Markdown"
            },
            timeout=20
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram Error: {e}")
        return False


def send_email_application(to_email, job_title, cover_letter, company="", cv_path=None):
    """
    Send job application via email.
    
    Args:
        to_email: Recipient email
        job_title: Job position title
        cover_letter: Generated cover letter
        company: Company name (optional)
    
    Returns:
        bool: Success status
    """
    
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("Missing SMTP credentials")
        return False
    if not to_email or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", str(to_email).strip()):
        print("Refusing to send: recipient email is invalid")
        return False

    # Require a verified CV file for automated applications. Never send a blank
    # application or silently claim success without the candidate's attachment.
    cv_path = cv_path or os.getenv("CV_FILE_PATH")
    if not cv_path or not os.path.isfile(cv_path):
        print("Refusing to send: CV_FILE_PATH is missing or the CV file is unavailable")
        return False
    allowed_extensions = {".pdf", ".doc", ".docx"}
    if os.path.splitext(cv_path)[1].lower() not in allowed_extensions:
        print("Refusing to send: CV must be PDF, DOC, or DOCX")
        return False
    if os.path.getsize(cv_path) > 10 * 1024 * 1024:
        print("Refusing to send: CV attachment exceeds 10 MB")
        return False

    try:
        # Construct email
        sender = SMTP_EMAIL
        subject = f"Application for {job_title} Position"
        
        # Create message
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = to_email
        msg["Subject"] = subject
        
        # Email body
        body = f"""Dear Hiring Manager,

{cover_letter}

Best regards,
Job Application System

---
This is an automated application. Please contact for further information.
"""
        
        msg.attach(MIMEText(body, "plain"))

        content_type, _ = mimetypes.guess_type(cv_path)
        maintype, subtype = (content_type or "application/octet-stream").split("/", 1)
        with open(cv_path, "rb") as cv_file:
            attachment = MIMEBase(maintype, subtype)
            attachment.set_payload(cv_file.read())
        encoders.encode_base64(attachment)
        attachment.add_header("Content-Disposition", "attachment", filename=os.path.basename(cv_path))
        msg.attach(attachment)
        
        # Send via SMTP
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(sender, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Email sending failed: {str(e)}")
        return False


def format_job_notification(job_data, decision_info, success=None):
    """
    Format comprehensive job notification for Telegram.
    
    Args:
        job_data: Job information dict
        decision_info: Application decision from decide_application_mode()
    
    Returns:
        Formatted message string
    """
    
    title = job_data.get("title", "Unknown Position")
    country = job_data.get("country", "Unknown")
    score = job_data.get("score", 0)
    priority_flags = job_data.get("priority_flags", [])
    link = job_data.get("link", "")
    source = job_data.get("source", "Unknown")
    
    mode = decision_info.get("mode", ApplicationMode.MANUAL_ALERT)
    confidence = decision_info.get("confidence_score", 0.0)
    reasoning = decision_info.get("reasoning", "")
    apply_email = decision_info.get("apply_email")
    apply_url = decision_info.get("apply_url")
    
    mode_emoji = get_mode_emoji(mode)
    confidence_display = format_confidence_display(confidence)
    flags_display = format_flags_display(priority_flags)
    
    # ==================
    # 🟢 AUTO_APPLY MODE
    # ==================
    if mode == ApplicationMode.AUTO_APPLY:
        status_line = ("✅ *Status:* Application email sent successfully" if success is True
                       else "❌ *Status:* Application was not confirmed as sent")
        message = f"""🚀 *AUTOMATIC APPLICATION*

*Position:* {title}
*Country:* 🌍 {country}
*Score:* {score}% 
*Source:* {source}

{confidence_display}

*Priority Flags:*
{flags_display}

📧 *Email:* {apply_email}
{status_line}

🔗 Job Link:
{link}

━━━━━━━━━━━━━━━━━━
*System Decision:* {reasoning}
"""

    # ==================
    # 🟡 GUIDED_APPLY MODE
    # ==================
    elif mode == ApplicationMode.GUIDED_APPLY:
        message = f"""🟡 *GUIDED APPLICATION*

*Position:* {title}
*Country:* 🌍 {country}
*Score:* {score}%
*Source:* {source}

{confidence_display}

*Priority Flags:*
{flags_display}

📌 *How to Apply:*
1️⃣ Open the link below
2️⃣ Click on "Apply Now" button
3️⃣ Upload your CV
4️⃣ Fill in required information
5️⃣ Submit application

🔗 Apply Link:
{apply_url}

━━━━━━━━━━━━━━━━━━
*System Decision:* {reasoning}
"""

    # ==================
    # 🔴 MANUAL_ALERT MODE
    # ==================
    else:
        email_line = f"\n📧 *Possible application email (verify first):* {apply_email}\n" if apply_email else ""
        message = f"""🔴 *MANUAL OPPORTUNITY*

*Position:* {title}
*Country:* 🌍 {country}
*Score:* {score}%
*Source:* {source}

*Priority Flags:*
{flags_display}
{email_line}
📌 *How to Apply:*
• Visit the job link below
• Search for this position manually
• Apply through company's careers page
• Check for application requirements

🔗 Job Link:
{link}

━━━━━━━━━━━━━━━━━━
*System Note:* {reasoning}
"""

    return message


def notify_job_sent(job_data, decision_info, success=True):
    """
    Send job notification to Telegram.
    
    Args:
        job_data: Job information
        decision_info: Application decision
        success: Whether operation succeeded
    
    Returns:
        bool: Success status
    """
    
    message = format_job_notification(job_data, decision_info, success=success)
    
    if not success:
        message = f"⚠️ *APPLICATION FAILED*\n\n{message}\n\n❌ Error during processing"
    
    return send_message(message)


def notify_error(error_message: str):
    """Send error notification to admin"""
    message = f"❌ *System Error*\n\n{error_message}"
    return send_message(message)


def notify_summary(sent_count, skipped_count, failed_count):
    """Send daily summary to Telegram"""
    message = f"""✅ *Daily Job Processing Complete*

📊 *Statistics:*
• Sent: {sent_count}
• Skipped (low score): {skipped_count}
• Failed: {failed_count}

━━━━━━━━━━━━━━━━━━
Next run: Tomorrow 00:00 UTC
"""
    return send_message(message)
