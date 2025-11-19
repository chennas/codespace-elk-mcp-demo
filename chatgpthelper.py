import requests

# ⬇⬇⬇ CHANGE ONLY THIS LINE ⬇⬇⬇
MCP_URL = "https://psychic-space-capybara-9gv6x6qg4rfx66r-4040.app.github.dev/asksimplified"
# ⬆⬆⬆ CHANGE ONLY THIS LINE ⬆⬆⬆


def ask_mcp(question: str):
    """
    Sends natural-language questions to your MCP server
    and returns parsed JSON results.
    """
    try:
        response = requests.post(MCP_URL, json={"text": question})
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        return {"error": str(e)}


def ask(question: str):
    """
    Pretty-print helper used inside ChatGPT for display.
    """
    print(f"📨 Asking MCP: {question}\n")
    result = ask_mcp(question)

    if "error" in result:
        print("❌ Error:", result["error"])
    else:
        print("✅ Response from MCP:\n")
        print(result)

    return result


# --- TEST (You can comment these out) ---
# ask("Show failed users in last 1 hour")
# ask("Show top 3 failed users today")
# ask("Show attempts for username bob9")
