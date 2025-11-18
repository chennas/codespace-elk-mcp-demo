# codespace-elk-mcp-demo

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

