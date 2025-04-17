#!/bin/bash
# Script to restart Docker containers with original configuration

# Set execute permission for this script
chmod +x "$0"

# Stop all containers
echo "Stopping all containers..."
docker-compose down

# Start containers using the original configuration
echo "Starting containers with original configuration..."
docker-compose up -d

# Wait for services to start
echo "Waiting for services to start..."
sleep 10

# Check status
echo "Checking container status..."
docker-compose ps

echo -e "\nDone. Original hostname-based configuration has been restored." 