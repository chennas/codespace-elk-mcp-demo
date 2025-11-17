from flask import Flask, request, jsonify
import requests
from collections import Counter
from datetime import datetime, timedelta

app = Flask(__name__)

ES_URL = "http://elasticsearch:9200/app-logs-*/_search"

@app.route("/analyze")
def analyze():
    minutes = int(request.args.get("minutes", 60))
    start_time = (datetime.utcnow() - timedelta(minutes=minutes)).isoformat()

    query = {
        "query": {
            "range": {
                "timestamp": {"gte": start_time}
            }
        },
        "size": 200
    }

    response = requests.post(ES_URL, json=query).json()
    hits = response.get("hits", {}).get("hits", [])

    messages = [h["_source"]["message"] for h in hits if "message" in h["_source"]]

    word_counts = Counter(" ".join(messages).split())
    top_words = word_counts.most_common(5)

    return jsonify({
        "total_logs": len(messages),
        "top_words": top_words,
        "sample": messages[:3]
    })

@app.route("/")
def home():
    return "MCP analyzer running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
