from flask import Flask, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

LOG_FILE = "/logs/app.log"

@app.route("/generate", methods=["POST"])
def generate_log():
    data = request.get_json()
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": data.get("level", "INFO"),
        "message": data.get("message", "Hello from the app!")
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return jsonify({"status": "log written", "entry": entry})

@app.route("/")
def home():
    return "Simple Logging App Running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
