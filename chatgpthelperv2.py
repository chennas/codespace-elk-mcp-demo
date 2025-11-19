import requests
from tabulate import tabulate  # pip install tabulate if not installed

MCP_URL = "https://psychic-space-capybara-9gv6x6qg4rfx66r-4040.app.github.dev/asksimplified"

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

def print_table_from_dict_list(data_list: list):
    """
    Detects columns from a list of dictionaries and prints a pretty table.
    """
    if not data_list:
        print("⚠️ No data to display.")
        return
    headers = list(data_list[0].keys())
    table = [list(item.values()) for item in data_list]
    print(tabulate(table, headers=headers, tablefmt="grid"))

def ask(question: str):
    """
    Sends a question to MCP and displays the result nicely.
    """
    print(f"📨 Asking MCP: {question}\n")
    result = ask_mcp(question)

    if "error" in result:
        print("❌ Error:", result["error"])
    else:
        printed = False
        # Automatically detect any key whose value is a list of dictionaries
        for key, value in result.items():
            if isinstance(value, list) and value and all(isinstance(i, dict) for i in value):
                print(f"✅ {key.replace('_', ' ').title()}:\n")
                print_table_from_dict_list(value)
                printed = True
        # Fallback if nothing matches the list-of-dicts format
        if not printed:
            print("✅ Response from MCP:\n")
            print(result)

    return result

# --- TEST EXAMPLES ---
# ask("Show failed users in last 1 hour")
# ask("Show top 3 failed users today")
# ask("Show all login attempts today")
