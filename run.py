import os

os.system("cd filebeat && sudo chown 0:0 filebeat.yml && sudo chmod 644 filebeat.yml")
os.system("docker-compose up -d --build")
