# demo_workflow/workflow_demo.py
import requests
import csv
from prettytable import PrettyTable

# MCP server URL
MCP_URL = "http://localhost:8000/asksimplified"

def ask_mcp_direct(question: str):
    payload = {"text": question}
    try:
        res = requests.post(MCP_URL, json=payload)
        return res.json().get("results", [])
    except Exception as e:
        print("Error:", e)
        return []

def export_failed_users_csv(failed_users, csv_file="failed_users.csv"):
    with open(csv_file, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Username"])
        for user in failed_users:
            writer.writerow([user])
    print(f"CSV exported: {csv_file}")

def display_failed_users_table(failed_users):
    table = PrettyTable()
    table.field_names = ["Failed Users (Last 1 Hour)"]
    for user in failed_users:
        table.add_row([user])
    print(table)

# Example run
if __name__ == "__main__":
    users = ask_mcp_direct("Show failed users in last 1 hour")
    export_failed_users_csv(users)
    display_failed_users_table(users)
