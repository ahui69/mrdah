#!/bin/bash
pkill -f "python.*8080"
sleep 2
cd /home/ubuntu/mrd
AUTH_TOKEN="" nohup python3 -m core.app --port 8080 > /tmp/server.log 2>&1 &
echo "Server starting..."
sleep 4
echo "Checking status..."
curl -s http://localhost:8080/api/chat/assistant/status
