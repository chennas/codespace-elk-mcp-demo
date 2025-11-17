#!/usr/bin/env python3
"""
enterprise_log_generator.py - patched & hardened version

Replaces the previous script. Fixes:
- weights mismatch for random.choices
- safe payload handling in send()
- thread exception isolation
- clearer console logs and error handling
"""

import requests
import random
import time
import json
import uuid
import threading
import socket
from datetime import datetime, timedelta, timezone

# -----------------------------
# CONFIG
# -----------------------------
API_URL = "http://localhost:5000/generate"  # <-- update to your endpoint or Codespaces forwarded URL
SEND_IN_JSON = True      # if False, will send plain text payload (still sends JSON body with "message")
BURST_MIN = 5
BURST_MAX = 50
BURST_INTERVAL_MIN = 120
BURST_INTERVAL_MAX = 300
BACKGROUND_FREQ_MIN = 3
BACKGROUND_FREQ_MAX = 12
POISSON_SPIKE_PROB = 0.08
VERBOSE = True
TIMEZONE = timezone.utc
HTTP_TIMEOUT = 5  # seconds for requests.post

# -----------------------------
# DATA SOURCES
# -----------------------------
USERS = [
    "alice@example.com","bob@example.com","charlie@example.com","diana@example.com",
    "emily@example.com","frank@example.com","george@example.com","harry@example.com",
    "ivy@example.com","john.doe@example.com","jane.doe@example.com"
]

SERVICES = [
    "auth-service","payment-service","notification-service","order-service",
    "inventory-service","gateway-api","analytics-engine","user-service",
    "billing-service","reporting-service"
]

K8S_NAMESPACES = ["default","prod","staging","canary","monitoring"]
CONTAINERS = ["container-a","container-b","container-c"]

HTTP_METHODS = ["GET","POST","PUT","DELETE","PATCH"]
HTTP_RESPS = [200,201,202,204,301,302,400,401,403,404,409,429,500,502,503,504]
HTTP_PATHS = ["/api/v1/users","/api/v1/orders","/api/v1/payments","/api/v1/auth/login","/health","/metrics"]

KAFKA_TOPICS = ["orders","payments","user-events","audit-log"]
REDIS_KEYS = ["session_*","cart_*","cache_*"]
FEATURE_FLAGS = ["new-checkout","discount-experiment","search-v2"]

# -----------------------------
# HELPERS
# -----------------------------
def now_iso():
    return datetime.now(TIMEZONE).isoformat()

def drifted_timestamp(max_seconds=600):
    drift = random.randint(-max_seconds, 5)
    return (datetime.now(TIMEZONE) + timedelta(seconds=drift)).isoformat()

def gen_uuid():
    return str(uuid.uuid4())

def random_ip():
    return f"{random.randint(10,250)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

def choose(lst):
    return random.choice(lst)

def latency_ms(mean=120, std=60, floor=5):
    v = max(floor, int(random.gauss(mean, std)))
    return v

def sql_sample(svc):
    queries = [
        f"SELECT id, name FROM users WHERE email='{choose(USERS)}' LIMIT 1",
        "INSERT INTO payments (user_id, amount, status) VALUES (1234, 49.99, 'processed')",
        "UPDATE orders SET status='shipped' WHERE id=5678",
        "SELECT * FROM orders WHERE created_at > NOW() - interval '1 day' ORDER BY created_at DESC LIMIT 100"
    ]
    return choose(queries)

# -----------------------------
# LOG TEMPLATES
# -----------------------------
def access_log_line(ip, method, path, status, latency):
    ts = datetime.now().strftime("%d/%b/%Y:%H:%M:%S %z")
    return f'{ip} - - [{ts}] "{method} {path} HTTP/1.1" {status} {random.randint(120,4500)} "-" "curl/7.x" {latency}ms'

def app_log_json(service, level, message, extra=None):
    base = {
        "@timestamp": now_iso(),
        "service": service,
        "level": level,
        "message": message,
        "host": socket.gethostname(),
        "trace_id": gen_uuid(),
        "span_id": gen_uuid()[:16],
        "request_id": gen_uuid(),
        "pod_name": f"{service}-pod-{random.randint(1000,9999)}",
        "container": choose(CONTAINERS),
        "ip": random_ip()
    }
    if extra:
        base.update(extra)
    return base

def stack_trace_java():
    return ("NullPointerException: Attempted to access null reference\n"
            "    at com.example.app.UserController.getUser(UserController.java:58)\n"
            "    at com.example.app.AuthFilter.doFilter(AuthFilter.java:42)\n"
            "    at io.undertow.servlet.handlers.ServletInitialHandler.handleRequest(ServletInitialHandler.java:32)\n")

def stack_trace_python():
    return ("Traceback (most recent call last):\n"
            "  File \"/app/users.py\", line 78, in handle_request\n"
            "    user = db.get_user(email)\n"
            "  File \"/app/db.py\", line 22, in get_user\n"
            "    raise KeyError('user not found')\n"
            "KeyError: 'user not found'\n")

# -----------------------------
# EVENT GENERATORS
# -----------------------------
def gen_api_access_event():
    ip = random_ip()
    method = choose(HTTP_METHODS)
    path = choose(HTTP_PATHS)
    # Prepare safe weights: if you want custom weights, adjust base_weights below
    base_weights = [10,5,2,2,2,40,10,5,3,2,1,1,2,1,1]
    # Ensure weights length matches responses
    if len(base_weights) < len(HTTP_RESPS):
        base_weights += [2] * (len(HTTP_RESPS) - len(base_weights))
    elif len(base_weights) > len(HTTP_RESPS):
        base_weights = base_weights[:len(HTTP_RESPS)]
    status = random.choices(HTTP_RESPS, weights=base_weights, k=1)[0]
    lat = latency_ms(mean=180, std=140)
    if random.random() < 0.02:
        status = choose([500,502,503,504])
        lat *= random.randint(5,20)
    return {
        "type": "access",
        "format": "text",
        "message": access_log_line(ip, method, path, status, lat),
        "service": "nginx",
        "status": status,
        "ip": ip,
        "path": path,
        "method": method,
        "latency_ms": lat,
        "timestamp": drifted_timestamp(300)
    }

def gen_app_event():
    svc = choose(SERVICES)
    level = random.choices(["INFO","WARN","ERROR"], weights=[60,25,15], k=1)[0]
    if level == "INFO":
        msg = choose([
            f"User {choose(USERS)} created successfully",
            f"Background job completed, job_id={random.randint(1000,9999)}",
            f"Feature flag '{choose(FEATURE_FLAGS)}' evaluated to True for user {choose(USERS)}",
            f"Service {svc} heartbeat OK"
        ])
        extra = {"user": choose(USERS)}
    elif level == "WARN":
        msg = choose([
            f"Slow query detected: {sql_sample(svc)} took {latency_ms(mean=600)}ms",
            f"High memory usage: {random.randint(70,92)}% on {svc}",
            f"Retrying connection to redis cluster for key session_{random.randint(1000,9999)}"
        ])
        extra = {"service": svc}
    else:
        msg = choose([
            f"User {choose(USERS)} failed login",
            f"Unhandled exception in {svc}: {choose(['NullPointerException','IndexOutOfBoundsException','ValueError'])}",
            f"DatabaseTimeoutError in {svc}: query took {latency_ms(mean=2000)}ms",
            f"500 Internal Server Error in {svc} when calling /process"
        ])
        extra = {"service": svc}
    base = app_log_json(svc, level, msg, extra)
    if level == "ERROR" and random.random() < 0.5:
        base["stack_trace"] = stack_trace_java() if random.random() < 0.6 else stack_trace_python()
    base["@timestamp"] = drifted_timestamp(600)
    return {"type":"app","format":"json","payload": base}

def gen_k8s_event():
    svc = choose(SERVICES)
    pod = choose(K8S_PODS(svc)) if callable('K8S_PODS') else f"{svc}-pod-{random.randint(1000,9999)}"
    event = random.choice(["Started","StartedContainer","Killing","OOMKILLED","Evicted","BackOff","Scaled"])
    if event == "Started":
        msg = f"Started container {pod} in namespace {choose(K8S_NAMESPACES)}"
    elif event == "StartedContainer":
        msg = f"Started container {choose(CONTAINERS)} in pod {pod}"
    elif event == "Killing":
        msg = f"Killing container {choose(CONTAINERS)} in pod {pod} due to liveness probe failure"
    elif event == "OOMKILLED":
        msg = f"OOMKilled: Pod {pod} in namespace {choose(K8S_NAMESPACES)} was killed due to memory"
    elif event == "Evicted":
        msg = f"Pod {pod} evicted from node node-{random.randint(1,9)}"
    elif event == "BackOff":
        msg = f"Back-off restarting failed container in pod {pod}"
    else: # Scaled
        msg = f"HPA scaled deployment {svc} to {random.randint(1,10)} replicas"
    payload = {
        "type":"k8s",
        "format":"json",
        "message": msg,
        "pod": pod,
        "namespace": choose(K8S_NAMESPACES),
        "service": svc,
        "timestamp": drifted_timestamp(900)
    }
    return payload

def gen_kafka_event():
    topic = choose(KAFKA_TOPICS)
    if random.random() < 0.02:
        msg = f"Partition reassignment for topic {topic} - leaders moved"
    else:
        msg = f"Produced message to {topic} partition {random.randint(0,10)} offset {random.randint(1000,999999)}"
    return {"type":"kafka","format":"json","message":msg,"timestamp":drifted_timestamp(300)}

def gen_redis_event():
    if random.random() < 0.05:
        msg = f"Redis connection refused on node redis-{random.randint(1,3)}"
    else:
        key = choose(REDIS_KEYS).replace("*",str(random.randint(100,999)))
        msg = f"Cache miss for key {key}"
    return {"type":"redis","format":"json","message":msg,"timestamp":drifted_timestamp(200)}

def gen_cicd_event():
    stage = choose(["checkout","build","test","deploy"])
    status = choose(["SUCCESS","FAILURE","IN_PROGRESS"])
    msg = f"CI job {random.randint(1000,9999)} - stage {stage} - {status}"
    return {"type":"cicd","format":"json","message":msg,"timestamp":drifted_timestamp(600)}

def gen_feature_flag_event():
    flag = choose(FEATURE_FLAGS)
    user = choose(USERS)
    msg = f"Feature flag evaluation: {flag} -> OFF for user {user}"
    return {"type":"feature","format":"json","message":msg,"timestamp":drifted_timestamp(300)}

def gen_database_query_event():
    svc = choose(SERVICES)
    q = sql_sample(svc)
    latency = latency_ms(mean=300, std=200)
    err = None
    if latency > 2000:
        err = "QueryTimeoutError"
    return {"type":"sql","format":"json","message":q, "latency_ms": latency, "error": err, "service": svc, "timestamp": drifted_timestamp(400)}

# -----------------------------
# SENDER
# -----------------------------
def send(payload):
    """
    Safe sending helper. Handles:
    - payload with 'format' == 'text' and 'message'
    - payload with 'format' == 'json' and nested 'payload' dict
    - fallback for generic event dicts
    """
    try:
        if payload is None:
            if VERBOSE:
                print("[WARN] send called with None payload")
            return

        # If payload claims to be JSON structured and has 'payload' key
        if payload.get("format") == "json":
            body = payload.get("payload") if isinstance(payload.get("payload"), dict) else None
            # If body missing, construct from top-level keys
            if not body:
                body = {
                    "@timestamp": payload.get("timestamp", now_iso()),
                    "service": payload.get("service", "unknown"),
                    "level": payload.get("level", "INFO"),
                    "message": payload.get("message", "")
                }
        elif payload.get("format") == "text":
            body = {
                "message": payload.get("message", ""),
                "level": payload.get("level", "INFO"),
                "timestamp": payload.get("timestamp", now_iso())
            }
        else:
            # Generic dict event (may already be structured)
            if isinstance(payload.get("payload"), dict):
                body = payload["payload"]
            elif "message" in payload:
                body = {"message": payload.get("message"), "timestamp": payload.get("timestamp", now_iso())}
            else:
                # fallback: try to send the whole dict as message
                body = {"message": json.dumps(payload), "timestamp": now_iso()}

        headers = {"Content-Type": "application/json"}
        resp = requests.post(API_URL, data=json.dumps(body), headers=headers, timeout=HTTP_TIMEOUT)
        if VERBOSE:
            print(f"[SEND] {body.get('service','-')} | {body.get('level','-')} | {str(body.get('message'))[:140]} | status={getattr(resp, 'status_code', 'N/A')}")
    except Exception as e:
        # Do not raise — just log
        if VERBOSE:
            print(f"[ERROR - SEND FAILED] {e}")

# -----------------------------
# WORKERS & ORCHESTRATION
# -----------------------------
def safe_call(fn, *args, **kwargs):
    """Call fn with exception isolation and logging."""
    try:
        return fn(*args, **kwargs)
    except Exception as ex:
        if VERBOSE:
            print(f"[THREAD ERROR] {fn.__name__} raised: {ex}")

def burst_worker():
    try:
        burst_size = random.randint(BURST_MIN, BURST_MAX)
        for _ in range(burst_size):
            ev = random.choices([
                gen_api_access_event,
                gen_app_event,
                gen_k8s_event,
                gen_kafka_event,
                gen_redis_event,
                gen_cicd_event,
                gen_feature_flag_event,
                gen_database_query_event
            ], weights=[30,25,8,5,8,5,4,15], k=1)[0]()
            # send with isolated exception handling
            safe_call(send, ev)
            time.sleep(random.uniform(0.03, 0.45))
    except Exception as e:
        if VERBOSE:
            print(f"[BURST WORKER ERROR] {e}")

def background_worker():
    while True:
        try:
            ev = random.choices([gen_api_access_event, gen_app_event, gen_redis_event], weights=[50,35,15], k=1)[0]()
            safe_call(send, ev)
            time.sleep(random.uniform(BACKGROUND_FREQ_MIN, BACKGROUND_FREQ_MAX))
        except Exception as e:
            if VERBOSE:
                print(f"[BACKGROUND WORKER ERROR] {e}")
            time.sleep(1)

def orchestrator():
    while True:
        try:
            if random.random() < POISSON_SPIKE_PROB:
                spikes = random.randint(2,5)
                if VERBOSE:
                    print(f"*** SPIKE: scheduling {spikes} quick bursts")
                for _ in range(spikes):
                    threading.Thread(target=burst_worker, daemon=True).start()
                    time.sleep(random.uniform(0.5, 2))
            else:
                threading.Thread(target=burst_worker, daemon=True).start()

            wait = random.randint(BURST_INTERVAL_MIN, BURST_INTERVAL_MAX)
            if VERBOSE:
                print(f"[ORCH] sleeping {wait}s until next burst")
            time.sleep(wait)
        except Exception as e:
            if VERBOSE:
                print(f"[ORCHESTRATOR ERROR] {e}")
            time.sleep(5)

# -----------------------------
# MAIN
# -----------------------------
def main():
    print("Enterprise log generator starting (patched)...")
    threading.Thread(target=background_worker, daemon=True).start()
    threading.Thread(target=orchestrator, daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down log generator.")

if __name__ == "__main__":
    main()
