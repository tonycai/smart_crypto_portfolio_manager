#!/bin/bash
# Script to patch the URLs in the orchestration agent Docker container

# Set execute permission for this script
chmod +x "$0"

echo "Patching orchestration agent to use localhost URLs..."

# Get the container ID for the orchestration agent
CONTAINER_ID=$(docker ps | grep orchestration-agent | awk '{print $1}')
if [ -z "$CONTAINER_ID" ]; then
  echo "Error: Orchestration agent container not found"
  exit 1
fi

echo "Found orchestration agent container: $CONTAINER_ID"

# Create a simple script to update the agent URLs in the container
cat > patch_urls.py << 'EOF'
#!/usr/bin/env python3
"""
Script to patch the agent URLs in the orchestration agent
"""
import json
import os

# Agent configuration file to update
config_file = "/app/config/orchestration.json"

# Check if the config file exists
if not os.path.exists(config_file):
    print(f"Config file {config_file} not found")
    # Try to find a different config file
    config_dir = "/app/config"
    if os.path.exists(config_dir):
        print(f"Looking in {config_dir} for config files")
        for filename in os.listdir(config_dir):
            if filename.endswith(".json"):
                print(f"Found: {filename}")
    exit(1)

# Load the config
with open(config_file, 'r') as f:
    config = json.load(f)

# Update URLs
print("Original URLs:")
for key in config:
    if "agent_url" in key:
        print(f"  {key}: {config[key]}")

# Update the URLs to use localhost
updates = {
    "market_analysis_agent_url": "http://localhost:8001",
    "trade_execution_agent_url": "http://localhost:8002",
    "risk_management_agent_url": "http://localhost:8003",
    "reporting_analytics_agent_url": "http://localhost:8004"
}

for key, new_url in updates.items():
    if key in config:
        config[key] = new_url

# Save the updated config
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print("\nUpdated URLs:")
for key in config:
    if "agent_url" in key:
        print(f"  {key}: {config[key]}")

print("\nConfig updated successfully")

# Also patch the agent.py file to update the hard-coded URLs
agent_file = "/app/agents/orchestration/agent.py"
if os.path.exists(agent_file):
    print(f"\nPatching {agent_file}")
    
    # Read the file
    with open(agent_file, 'r') as f:
        content = f.read()
    
    # Replace container URLs with localhost
    replacements = [
        ("http://market-analysis-agent:", "http://localhost:"),
        ("http://trade-execution-agent:", "http://localhost:"),
        ("http://risk-management-agent:", "http://localhost:"),
        ("http://reporting-analytics-agent:", "http://localhost:")
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    # Write the updated file
    with open(agent_file, 'w') as f:
        f.write(content)
    
    print("Agent file patched successfully")
EOF

# Copy the script to the container
docker cp patch_urls.py $CONTAINER_ID:/app/patch_urls.py

# Make the script executable in the container
docker exec $CONTAINER_ID chmod +x /app/patch_urls.py

# Run the script in the container
docker exec $CONTAINER_ID python3 /app/patch_urls.py

echo "Patch applied. Restarting container..."

# Restart the container to apply the changes
docker restart $CONTAINER_ID

echo "Done. Container restarted. Please wait a few seconds for it to initialize."
echo "Then test with: ./test_mcp_functions.sh"

# Clean up
rm patch_urls.py 