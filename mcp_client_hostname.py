#!/usr/bin/env python3
"""
MCP Client - A simple client for interacting with the MCP server
For use with hostname-based orchestration agent configuration
"""

import argparse
import json
import requests
import sys
from typing import Dict, Any, Optional

class MCPClient:
    """Client for interacting with the MCP (Model Calling Protocol) server"""
    
    def __init__(self, server_url: str = "http://localhost:8005", api_key: Optional[str] = None):
        """Initialize the MCP client
        
        Args:
            server_url: Base URL for the MCP server
            api_key: Optional API key for authentication
        """
        self.server_url = server_url
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            self.headers["X-API-Key"] = api_key
    
    def call_function(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a function via the MCP protocol
        
        Args:
            function_name: Name of the function to call
            arguments: Arguments to pass to the function
            
        Returns:
            Response from the server
        """
        url = f"{self.server_url}/api/v1/mcp/function"
        payload = {
            "function": function_name,
            "arguments": arguments
        }
        
        response = requests.post(url, json=payload, headers=self.headers)
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            return {"error": response.text}
        
        return response.json()
    
    def get_all_agents_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        # Get all agents by not specifying a specific agent
        return self.call_function("get_agent_status", {})
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get status of a specific agent"""
        return self.call_function("get_agent_status", {"agent_name": agent_id})
    
    def execute_workflow(self, workflow_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow"""
        return self.call_function("execute_workflow", {
            "workflow_name": workflow_name,
            "parameters": parameters
        })
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status of a workflow"""
        return self.call_function("get_workflow_status", {"workflow_id": workflow_id})
    
    def run_health_check(self) -> Dict[str, Any]:
        """Check the health of the server"""
        try:
            response = requests.get(f"{self.server_url}/")
            if response.status_code == 200:
                return {"status": "healthy", "details": response.json()}
            else:
                return {"status": "unhealthy", "details": response.text}
        except Exception as e:
            return {"status": "error", "details": str(e)}
    
    def list_available_functions(self) -> Dict[str, Any]:
        """List all available functions"""
        # Make an intentionally invalid request to get the list of available functions
        result = self.call_function("__list_functions", {})
        if "available_functions" in result:
            return {"functions": result["available_functions"]}
        return {"error": "Could not retrieve available functions"}


def main():
    """Main function to run the client from command line"""
    parser = argparse.ArgumentParser(description="MCP Client")
    parser.add_argument("--server", default="http://localhost:8005", help="MCP server URL")
    parser.add_argument("--api-key", help="API key for authentication")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Get all agents status
    subparsers.add_parser("agents", help="Get status of all agents")
    
    # Get agent status
    agent_parser = subparsers.add_parser("agent", help="Get status of a specific agent")
    agent_parser.add_argument("agent_id", help="ID of the agent")
    
    # Execute workflow
    workflow_parser = subparsers.add_parser("workflow", help="Execute a workflow")
    workflow_parser.add_argument("workflow_name", help="Name of the workflow")
    workflow_parser.add_argument("--params", help="JSON string of parameters")
    
    # Get workflow status
    status_parser = subparsers.add_parser("status", help="Get status of a workflow")
    status_parser.add_argument("workflow_id", help="ID of the workflow")
    
    # Custom function call
    function_parser = subparsers.add_parser("function", help="Call a custom function")
    function_parser.add_argument("function_name", help="Name of the function")
    function_parser.add_argument("--args", help="JSON string of arguments")
    
    # Health check
    subparsers.add_parser("health", help="Check health of the server")
    
    # List available functions
    subparsers.add_parser("functions", help="List available functions")
    
    args = parser.parse_args()
    
    client = MCPClient(args.server, args.api_key)
    
    if args.command == "agents":
        result = client.get_all_agents_status()
    elif args.command == "agent":
        result = client.get_agent_status(args.agent_id)
    elif args.command == "workflow":
        params = json.loads(args.params) if args.params else {}
        result = client.execute_workflow(args.workflow_name, params)
    elif args.command == "status":
        result = client.get_workflow_status(args.workflow_id)
    elif args.command == "function":
        arguments = json.loads(args.args) if args.args else {}
        result = client.call_function(args.function_name, arguments)
    elif args.command == "health":
        result = client.run_health_check()
    elif args.command == "functions":
        result = client.list_available_functions()
    else:
        parser.print_help()
        return
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main() 