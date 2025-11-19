# codespace-elk-mcp-demo

docker-compose up -d filebeat


# start everything
docker-compose up -d --build

# show logs (optional)
docker-compose logs -f app filebeat logstash elasticsearch kibana mcp


# send a log via HTTP to the Flask app
curl -s -X POST http://localhost:5000/generate -H "Content-Type: application/json" \
  -d '{"message":"User john@example.com failed login", "level":"ERROR"}'


cd filebeat
sudo chown 0:0 filebeat.yml
sudo chmod 644 filebeat.yml

docker-compose up -d filebeat

Make your MCP server public
docker exec -it demo_mcp bash
uvicorn main:app --host 0.0.0.0 --port 8000
Ensure /asksimplified endpoint works locally inside the container:

curl -X POST http://localhost:8000/asksimplified -H "Content-Type: application/json" -d '{"text":"Show failed users in last 1 hour"}'

curl -X POST https://psychic-space-capybara-9gv6x6qg4rfx66r-8000.app.github.dev/asksimplified -H "Content-Type: application/json" -d '{"text":"Show failed users in last 1 hour"}'


curl -X POST https://psychic-space-capybara-9gv6x6qg4rfx66r-8000.app.github.dev/globalsearch -H "Content-Type: application/json" -d '{"text":"Show all logs containing timeout errors in last 2 hours"}'


Step 2: Install ngrok and expose MCP server
Install ngrok in Codespaces (or download the binary):
# Linux
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
chmod +x ngrok
./ngrok config add-authtoken YOUR_TOKEN_HERE
./ngrok http http://localhost:8000
./ngrok http 8000

Forward MCP server port 8000:
./ngrok http 8000
Copy the HTTPS public URL that ngrok provides, e.g.:
https://abcd1234.ngrok.io

Step 3: Update your Python MCP client

Change the MCP_URL to the ngrok HTTPS URL:

import requests

# Use ngrok URL
MCP_URL = "https://abcd1234.ngrok.io/asksimplified"

def ask_mcp(question: str):
    payload = {"text": question}
    try:
        response = requests.post(MCP_URL, json=payload)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    res = ask_mcp("Show failed users in last 1 hour")
    print(res)


Test it locally — it should return your simplified logs from MCP server.

Step 4: Use ChatGPT to query MCP

Now, in ChatGPT:

Use Python code execution / OpenAI Code Interpreter (or any notebook):

import requests

MCP_URL = "https://abcd1234.ngrok.io/asksimplified"

def ask_mcp(question: str):
    payload = {"text": question}
    response = requests.post(MCP_URL, json=payload)
    return response.json()

# Example queries
print(ask_mcp("Show failed users in last 1 hour"))
print(ask_mcp("Show top 3 failed users today"))


ChatGPT will execute the request and return JSON results from your MCP server.

✅ Key Notes

Do not use Codespaces preview URLs for WebSocket/POST endpoints, they often give 404/308.

ngrok gives a stable HTTPS endpoint accessible to ChatGPT.

You can now ask natural English questions in ChatGPT using this MCP client.

I can also provide a ready-to-use ChatGPT helper script that you just paste into a notebook and query MCP with natural questions, like:

"Show failed users in last 2 hours"
"Show successful users today"


…and it will return parsed JSON automatically.


https://psychic-space-capybara-9gv6x6qg4rfx66r-4040.app.github.dev/

