from fastapi import FastAPI
from pydantic import BaseModel
from elasticsearch import Elasticsearch
from datetime import datetime, timedelta
import os
import openai
from dotenv import load_dotenv
import json
import re

# Load OpenAI API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Connect to Elasticsearch
es = Elasticsearch(hosts=["http://elasticsearch:9200"])

app = FastAPI()

class Question(BaseModel):
    text: str

# ======================
# OpenAI NLP → ES query
# ======================
def parse_question_to_query(question: str):
    """
    Converts natural language question into Elasticsearch query JSON.
    Safe fallback if OpenAI response is invalid.
    """
    prompt = f"""
    Convert this English question into Elasticsearch query JSON for index 'app-logs-*'.
    Question: "{question}"
    Return only valid JSON, do not add explanations or extra text.
    """

    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=300,
            temperature=0
        )
        es_query_text = response.choices[0].text.strip()

        # Extract JSON using regex
        match = re.search(r"\{.*\}", es_query_text, re.DOTALL)
        if match:
            es_query_str = match.group(0)
            return json.loads(es_query_str)

    except Exception as e:
        print("OpenAI parsing error:", e)

    # fallback: simple query for last 1 hour
    return {
        "query": {
            "range": {
                "timestamp": {"gte": "now-1h"}
            }
        },
        "size": 10
    }

# ======================
# Full logs endpoint
# ======================
@app.post("/ask")
def ask(question: Question):
    query = parse_question_to_query(question.text)
    try:
        res = es.search(index="app-logs-*", body=query)
        # Keep only readable fields
        simplified_results = []
        for hit in res["hits"]["hits"]:
            source = hit["_source"]
            simplified_results.append({
                "timestamp": source.get("timestamp"),
                "app": source.get("app"),
                "message": source.get("message")
            })
        return {"results": simplified_results}
    except Exception as e:
        return {"error": str(e)}

# ======================
# Smart simplified endpoint
# ======================
def generate_es_query_for_simple_question(question_text):
    """
    Handles:
    - Failed users
    - Successful users
    - Top N failed users
    """
    question_text = question_text.lower()
    time_range = {"gte": "now-1h"}

    # Detect time expressions
    match = re.search(r"last (\d+) (hour|hours|day|days)", question_text)
    if match:
        num = int(match.group(1))
        unit = match.group(2)
        if "hour" in unit:
            time_range["gte"] = f"now-{num}h"
        elif "day" in unit:
            time_range["gte"] = f"now-{num}d"

    # Failed users
    if "failed" in question_text:
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"range": {"timestamp": time_range}},
                        {"match": {"message": "failed login"}}
                    ]
                }
            },
            "size": 100
        }
        # Top N failed users
        top_match = re.search(r"top (\d+)", question_text)
        if top_match:
            query["size"] = int(top_match.group(1))
        return query

    # Successful users
    elif "successful" in question_text or "success" in question_text:
        return {
            "query": {
                "bool": {
                    "must": [
                        {"range": {"timestamp": time_range}},
                        {"match": {"message": "created successfully"}}
                    ]
                }
            },
            "size": 100
        }

    # Default fallback
    return {
        "query": {"range": {"timestamp": time_range}},
        "size": 10
    }

@app.post("/asksimplified")
def ask_simplified(question: Question):
    query = generate_es_query_for_simple_question(question.text)
    try:
        res = es.search(index="app-logs-*", body=query)
        simplified_results = []
        for hit in res["hits"]["hits"]:
            msg = hit["_source"].get("message", "")
            match = re.search(r"User (\S+)", msg)
            if match:
                simplified_results.append(match.group(1))
        return {"results": simplified_results}
    except Exception as e:
        return {"error": str(e)}

# ======================
# Global search endpoint (AI-agent + time-aware)
# ======================
@app.post("/globalsearch")
def global_search_nlp(question: Question):
    """
    AI-agent-friendly global search.
    Accepts natural language questions, parses them to ES queries,
    supports partial/like match in 'message', and handles time ranges.
    
    Example questions:
        - "Show all logs containing timeout errors in last 2 hours"
        - "Find failed login attempts in last 1 day"
    """
    search_text = question.text.strip()
    if not search_text:
        return {
            "error": "Please provide a natural language question in 'text'."
        }

    # Step 1: Default time range: last 1 hour
    time_range = {"gte": "now-1h"}
    match = re.search(r"last (\d+)\s*(hour|hours|day|days)", search_text, re.IGNORECASE)
    if match:
        num = int(match.group(1))
        unit = match.group(2).lower()
        if "hour" in unit:
            time_range["gte"] = f"now-{num}h"
        elif "day" in unit:
            time_range["gte"] = f"now-{num}d"

    # Step 2: Build Elasticsearch query
    query = {
        "query": {
            "bool": {
                "must": [
                    {"range": {"timestamp": time_range}},
                    {
                        "query_string": {
                            "fields": ["message"],
                            "query": f"*{search_text}*",
                            "analyze_wildcard": True
                        }
                    }
                ]
            }
        },
        "size": 50,  # default number of results
        "sort": [{"timestamp": {"order": "desc"}}]
    }

    # Step 3: Execute search
    try:
        res = es.search(index="app-logs-*", body=query)
        results = []
        for hit in res["hits"]["hits"]:
            src = hit["_source"]
            results.append({
                "timestamp": src.get("timestamp"),
                "app": src.get("app"),
                "level": src.get("level"),
                "message": src.get("message")
            })
        return {"results": results, "count": len(results)}

    except Exception as e:
        return {"error": str(e)}
