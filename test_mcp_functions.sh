#!/bin/bash
# Script to test various MCP functions

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

# Test get_agent_status (all agents)
echo -e "===== Testing get_agent_status (all agents) =====\n"
call_mcp_function "get_agent_status" "{}"

# Test get_agent_status (specific agent)
echo -e "===== Testing get_agent_status (Trade Execution Agent) =====\n"
call_mcp_function "get_agent_status" "{\"agent_name\": \"Trade Execution Agent\"}"

# Test execute_market_analysis
echo -e "===== Testing execute_market_analysis =====\n"
call_mcp_function "execute_market_analysis" "{\"crypto_pair\": \"BTC/USD\", \"timeframe\": \"4h\"}"

# Test assess_risk
echo -e "===== Testing assess_risk =====\n"
call_mcp_function "assess_risk" "{\"portfolio\": {\"BTC\": 0.5, \"ETH\": 0.3, \"SOL\": 0.2}}"

# Test execute_trade
echo -e "===== Testing execute_trade =====\n"
call_mcp_function "execute_trade" "{\"crypto_pair\": \"BTC/USD\", \"action\": \"buy\", \"amount\": 0.1}"

# Test generate_report
echo -e "===== Testing generate_report =====\n"
call_mcp_function "generate_report" "{\"report_type\": \"performance\", \"timeframe\": \"1w\"}"

# Test execute_workflow
echo -e "===== Testing execute_workflow (portfolio_rebalance) =====\n"
call_mcp_function "execute_workflow" "{\"workflow_name\": \"portfolio_rebalance\", \"parameters\": {\"risk_tolerance\": \"medium\", \"target_assets\": [\"BTC\", \"ETH\", \"SOL\"]}}"

echo -e "Tests completed." 