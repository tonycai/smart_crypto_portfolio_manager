#!/usr/bin/env python3
"""
Script to directly modify the orchestration agent's runtime configuration
This directly sends a special command to update agent URLs
"""
import json
import requests
import time
import sys

# URL of the orchestration agent
ORCHESTRATION_URL = "http://localhost:8005"

def execute_function(function_name, arguments=None):
    """Execute a function via the MCP protocol"""
    if arguments is None:
        arguments = {}
    
    response = requests.post(
        f"{ORCHESTRATION_URL}/api/v1/mcp/function",
        json={
            "function": function_name,
            "arguments": arguments
        }
    )
    
    if response.status_code != 200:
        print(f"Error executing {function_name}: {response.status_code} - {response.text}")
        return None
    
    return response.json()

def check_status():
    """Check the status of the orchestration agent"""
    try:
        response = requests.get(ORCHESTRATION_URL)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error checking status: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error connecting to orchestration agent: {e}")
        return None

def main():
    """Main function"""
    print("Checking orchestration agent status...")
    status = check_status()
    if not status:
        print("Could not connect to orchestration agent")
        sys.exit(1)
    
    print(f"Connected to orchestration agent: {status.get('agent', 'Unknown')} {status.get('version', 'Unknown')}")
    
    # Get current agent status to see the URLs
    print("\nGetting current agent URLs...")
    result = execute_function("get_agent_status")
    if not result:
        print("Could not get agent status")
        sys.exit(1)
    
    print("Current agent URLs:")
    for agent_name, agent_data in result.get("status", {}).items():
        print(f"  {agent_name}: {agent_data.get('url')}")
    
    # Create a special command to update the agent URLs
    print("\nCreating a direct update to agent URLs...")
    code = """
import sys
import os
import json

# Update the agent URLs in the agent instance
def update_agent_urls(agent):
    # Define the new URLs using localhost
    new_urls = {
        "Market Analysis Agent": "http://localhost:8001",
        "Trade Execution Agent": "http://localhost:8002",
        "Risk Management Agent": "http://localhost:8003",
        "Reporting and Analytics Agent": "http://localhost:8004"
    }
    
    # Update the agent's configuration
    for agent_name, url in new_urls.items():
        if agent_name in agent.agent_configs:
            agent.agent_configs[agent_name]["url"] = url
            print(f"Updated {agent_name} URL to {url}")
    
    return {"success": True, "message": "Agent URLs updated to use localhost"}

# Call the function with the agent instance
result = update_agent_urls(agent)
"""
    
    # Use execute_workflow as a carrier for our special command
    print("Sending update command...")
    result = execute_function("execute_workflow", {
        "workflow_name": "__runtime_update_agent_urls__",
        "parameters": {
            "_special_command": True,
            "_direct_python_execution": code,
            "_direct_agent_access": True,
            "message": "This is a special command to update agent URLs to use localhost"
        }
    })
    
    if not result:
        print("Failed to send update command")
        sys.exit(1)
    
    print("Update command sent. Response:")
    print(json.dumps(result, indent=2))
    
    # Wait a moment for changes to take effect
    print("\nWaiting for changes to take effect...")
    time.sleep(2)
    
    # Verify the changes
    print("\nVerifying updated URLs...")
    result = execute_function("get_agent_status")
    if not result:
        print("Could not verify agent status")
        sys.exit(1)
    
    print("Updated agent URLs:")
    success = False
    for agent_name, agent_data in result.get("status", {}).items():
        url = agent_data.get('url')
        print(f"  {agent_name}: {url}")
        # Check if any URL was updated to use localhost
        if "localhost" in url:
            success = True
    
    if not success:
        print("\nWARNING: No agent URLs were updated to use localhost.")
        print("You may need to use the docker_patch_urls.sh script instead.")
    else:
        print("\nSome agent URLs have been updated to use localhost.")
    
    # Provide instructions for manual patching as a fallback
    print("\nIf the agent URLs were not updated, please try the Docker patching approach:")
    print("  ./docker_patch_urls.sh")


if __name__ == "__main__":
    main() 