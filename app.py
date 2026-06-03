from flask import Flask
import requests
import os

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        response = requests.post(url, data=payload)

        # 👇 هذا أهم سطر للتشخيص
        print("Telegram response:", response.text)

        return response.text

    except Exception as e:
        print("ERROR:", str(e))
        return str(e)


@app.route("/")
def home():
    return "Bot is running 🚀"


@app.route("/test")
def test():
    result = send_telegram("🔥 Test message from Render Bot")

    return f"Sent! Response: {result}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
