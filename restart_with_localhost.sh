#!/bin/bash
# Script to restart Docker containers with localhost configuration

# Set execute permission for this script
chmod +x "$0"

# Stop all containers
echo "Stopping all containers..."
docker-compose down

# Start containers using the localhost configuration
echo "Starting containers with localhost configuration..."
docker-compose -f docker-compose-localhost.yml up -d

# Wait for services to start
echo "Waiting for services to start..."
sleep 10

# Check status
echo "Checking container status..."
docker-compose ps

echo -e "\nDone. Testing agent connectivity..."
./test_mcp_functions.sh 