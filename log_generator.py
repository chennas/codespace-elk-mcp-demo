import requests
import random
import time
import json
from datetime import datetime, timezone

API_URL = "http://localhost:5000/generate"  # <-- update to forwarded URL if using Codespaces

USERS = [
    "alice@example.com", "bob@example.com", "charlie@example.com",
    "diana@example.com", "emily@example.com", "frank@example.com",
    "george@example.com", "harry@example.com", "ivy@example.com"
]

INFO_MESSAGES = [
    "User {user} created successfully",
    "User {user} updated profile",
    "Cron job 'cleanup_temp_files' executed successfully",
    "Email notification sent to {user}",
    "Background worker completed job ID {job}"
]

ERROR_MESSAGES = [
    "User {user} failed login",
    "NullPointerException: Attempted to access null reference",
    "500 Internal Server Error: Unexpected application crash",
    "DatabaseTimeoutError: Query timed out after 30 seconds",
    "BadRequest: Received malformed payload from {user}",
    "NetworkError: Unable to reach authentication service",
    "AuthTokenExpired: Token expired for user {user}",
]

WARN_MESSAGES = [
    "High memory usage detected: 85%",
    "Slow query detected for user {user}",
    "Retrying connection to database...",
    "Cache miss for key: session_{user}",
]


def generate_log():
    level = random.choice(["INFO", "ERROR", "WARN"])
    user = random.choice(USERS)
    job = random.randint(1000, 9999)

    if level == "INFO":
        msg_template = random.choice(INFO_MESSAGES)
    elif level == "ERROR":
        msg_template = random.choice(ERROR_MESSAGES)
    else:
        msg_template = random.choice(WARN_MESSAGES)

    message = msg_template.format(user=user, job=job)

    payload = {
        "message": message,
        "level": level,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    return payload


def send_log(payload):
    try:
        response = requests.post(API_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"})
        print(f"[{payload['level']}] Sent: {payload['message']} | Status: {response.status_code}")
    except Exception as e:
        print(f"Failed to send log: {e}")


def main():
    print("=== Log Generator Started ===")
    while True:
        send_log(generate_log())
        time.sleep(random.randint(120, 180))  # 2–3 minutes


if __name__ == "__main__":
    main()
