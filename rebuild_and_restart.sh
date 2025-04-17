#!/bin/bash
echo "Stopping containers..."
docker-compose down

echo "Rebuilding containers..."
docker-compose build

echo "Starting containers..."
docker-compose up -d

echo "Waiting for services to start..."
sleep 5

echo "Checking agent status..."
python3 mcp_client_hostname.py --server http://localhost:8005 agents 