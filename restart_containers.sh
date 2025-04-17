#!/bin/bash
# Script to restart Docker containers

# Set execute permission for this script
chmod +x "$0"

# Stop all containers
echo "Stopping all containers..."
docker-compose down

# Apply configuration changes
echo "Applying configuration changes..."

# Update any configuration files to use localhost
if [ -f "config/orchestration.json" ]; then
  echo "Updating orchestration.json..."
  python3 update_agent_config.py config/orchestration.json
fi

# Start containers again
echo "Starting containers..."
docker-compose up -d

# Wait for services to start
echo "Waiting for services to start..."
sleep 10

# Check status
echo "Checking container status..."
docker-compose ps

echo -e "\nDone. You can now use the MCP client to interact with the agents." 