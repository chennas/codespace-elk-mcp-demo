# demo_workflow/copilot_queries.py
import json
from collections import Counter
from prettytable import PrettyTable
from workflow_demo import ask_mcp_direct

# Ask MCP for last 19 hour failed users
failed_users = ask_mcp_direct("Show failed users in last 19 hour")

# Count occurrences and get top 3
user_counts = Counter(failed_users)
top_3 = user_counts.most_common(3)

# Display in table
table = PrettyTable()
table.field_names = ["Rank", "Username", "Failure Count"]
for idx, (user, count) in enumerate(top_3, 1):
    table.add_row([idx, user, count])

print("Top 3 Failed Users (Last 19 Hours)")
print(table)

# Export to JSON
output = {
    "filter": "top 3 failed users",
    "time_range": "last 19 hours",
    "total_failures": len(failed_users),
    "top_3_users": [{"rank": i, "username": user, "failures": count} for i, (user, count) in enumerate(top_3, 1)]
}

with open("top_3_failed_users.json", "w") as f:
    json.dump(output, f, indent=2)

print("\n✅ Exported to top_3_failed_users.json")
print(json.dumps(output, indent=2))