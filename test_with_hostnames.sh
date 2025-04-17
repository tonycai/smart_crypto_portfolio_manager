#!/bin/bash
# Script to test hostname-based MCP configuration

# Set execute permission for this script
chmod +x "$0"

# Function to call MCP endpoint
call_mcp_function() {
  local function_name="$1"
  local arguments="$2"
  
  echo "Calling function: $function_name"
  echo "Arguments: $arguments"
  
  curl -s -X POST http://localhost:8005/api/v1/mcp/function \
    -H "Content-Type: application/json" \
    -d "{\"function\": \"$function_name\", \"arguments\": $arguments}"
  
  echo -e "\n"
}

# Test agent status
echo -e "===== Testing get_agent_status (all agents) =====\n"
call_mcp_function "get_agent_status" "{}"

# Test executing a workflow
echo -e "===== Testing execute_workflow (portfolio_rebalance) =====\n"
call_mcp_function "execute_workflow" "{\"workflow_name\": \"portfolio_rebalance\", \"parameters\": {\"risk_tolerance\": \"medium\", \"target_assets\": [\"BTC\", \"ETH\", \"SOL\"]}}"

echo -e "Configuration is now using hostnames."
echo "For client applications, continue to use http://localhost:8005 to connect to the orchestration agent."
echo "The orchestration agent will use container hostnames internally to communicate with other agents." 