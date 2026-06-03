from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Job Agent is Running 🚀"

@app.route("/test")
def test():
    return "Test OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
