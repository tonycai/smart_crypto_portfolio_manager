#!/usr/bin/env python3
"""
Script to update the orchestration agent's agent URLs via its API
This provides a direct way to fix the agent URLs without restarting containers
"""
import json
import requests
import sys

def update_agent_urls():
    """Update agent URLs to use localhost instead of container hostnames"""
    print("Updating agent URLs to use localhost...")
    
    # First, get current agent status to see the URLs
    response = requests.post(
        "http://localhost:8005/api/v1/mcp/function",
        json={"function": "get_agent_status", "arguments": {}}
    )
    
    if response.status_code != 200:
        print(f"Error getting agent status: {response.status_code} - {response.text}")
        return False
    
    result = response.json()
    print("Current agent URLs:")
    for agent_name, agent_data in result.get("status", {}).items():
        print(f"  {agent_name}: {agent_data.get('url')}")
    
    # Now, create a special function to update the URLs
    # We'll use the existing execute_workflow function to carry our special payload
    print("\nUpdating agent URLs...")
    
    new_urls = {
        "Market Analysis Agent": "http://localhost:8001",
        "Trade Execution Agent": "http://localhost:8002",
        "Risk Management Agent": "http://localhost:8003",
        "Reporting and Analytics Agent": "http://localhost:8004"
    }
    
    # Use execute_workflow as a carrier for our special command
    response = requests.post(
        "http://localhost:8005/api/v1/mcp/function",
        json={
            "function": "execute_workflow",
            "arguments": {
                "workflow_name": "update_agent_urls",
                "parameters": {
                    "agent_urls": new_urls,
                    "_special_command": "update_agent_urls"
                }
            }
        }
    )
    
    if response.status_code != 200:
        print(f"Error updating agent URLs: {response.status_code} - {response.text}")
        return False
    
    print("Agent URLs update requested. Response:")
    print(json.dumps(response.json(), indent=2))
    
    # Check if the update worked
    print("\nVerifying updated URLs...")
    response = requests.post(
        "http://localhost:8005/api/v1/mcp/function",
        json={"function": "get_agent_status", "arguments": {}}
    )
    
    if response.status_code != 200:
        print(f"Error verifying agent URLs: {response.status_code} - {response.text}")
        return False
    
    result = response.json()
    print("Updated agent URLs:")
    success = True
    for agent_name, agent_data in result.get("status", {}).items():
        url = agent_data.get('url')
        print(f"  {agent_name}: {url}")
        # Check if the URL was updated to use localhost
        if "localhost" not in url and agent_name in new_urls:
            success = False
    
    if not success:
        print("\nWARNING: Some agent URLs were not updated to use localhost.")
        print("You may need to manually update the orchestration agent's code or configuration.")
    else:
        print("\nAll agent URLs have been updated to use localhost.")
    
    return success


if __name__ == "__main__":
    update_agent_urls() 