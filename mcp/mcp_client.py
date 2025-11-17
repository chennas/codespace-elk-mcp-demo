import requests

MCP_URL = "http://localhost:8000/asksimplified"  # or Codespaces public URL

def ask_mcp(question: str):
    payload = {"text": question}
    try:
        response = requests.post(MCP_URL, json=payload)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# Example usage
if __name__ == "__main__":
    res = ask_mcp("Show failed users in last 19 hour")
    if "results" in res:
        from collections import Counter
        filtered = [user for user in res["results"] if user.startswith("bob9")]
        counts = Counter(filtered)
        top_3 = counts.most_common(3)
        print(top_3)
    else:
        print(res)
