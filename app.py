from flask import Flask, request
import requests
import os

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
YOUR_CHAT_ID = os.getenv("YOUR_CHAT_ID")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


# ========== إرسال رسالة ==========
def send_message(chat_id, text):
    requests.post(f"{TELEGRAM_API}/sendMessage", data={
        "chat_id": chat_id,
        "text": text
    })


# ========== إرسال أي نوع محتوى ==========
def forward_to_admin(user, content):
    msg = f"""
📩 رسالة جديدة للبوت:

👤 الاسم: {user.get('first_name')}
🔗 اليوزر: @{user.get('username')}
🆔 Chat ID: {user.get('id')}

💬 المحتوى:
{content}
"""
    send_message(YOUR_CHAT_ID, msg)


# ========== استقبال التحديثات ==========
@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()

    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        user = msg["from"]

        # أمر start
        if msg.get("text") == "/start":
            send_message(chat_id, "أهلاً 👋\nارسل رسالتك وبتوصل للدعم")
            return "ok"

        # نص
        if "text" in msg:
            forward_to_admin(user, msg["text"])

        # صور
        elif "photo" in msg:
            forward_to_admin(user, "📷 صورة")

        # ملفات
        elif "document" in msg:
            forward_to_admin(user, "📄 ملف")

        # صوت
        elif "voice" in msg:
            forward_to_admin(user, "🎤 صوت")

        # فيديو
        elif "video" in msg:
            forward_to_admin(user, "🎥 فيديو")

    return "ok"


# ========== إرسال رد من عندك ==========
@app.route("/reply", methods=["POST"])
def reply():
    data = request.get_json()

    user_id = data.get("chat_id")
    text = data.get("text")

    send_message(user_id, f"📩 رد من الدعم:\n\n{text}")

    return {"status": "sent"}


# ========== تشغيل السيرفر ==========
@app.route("/")
def home():
    return "Bot is running 🚀"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
