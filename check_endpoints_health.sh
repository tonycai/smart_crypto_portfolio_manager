#!/bin/bash
# Script to check health of all agents

# Set execute permission for this script
chmod +x "$0"

# Print health check for root endpoints
echo "Checking base health endpoints..."
echo -e "\nMarket Analysis Agent (8001):"
curl -s http://localhost:8001/
echo -e "\n\nTrade Execution Agent (8002):"
curl -s http://localhost:8002/
echo -e "\n\nRisk Management Agent (8003):"
curl -s http://localhost:8003/
echo -e "\n\nReporting Analytics Agent (8004):"
curl -s http://localhost:8004/
echo -e "\n\nOrchestration Agent (8005):"
curl -s http://localhost:8005/

echo -e "\n\nChecking MCP function endpoints..."
echo -e "\nCalling orchestration agent MCP function:"
curl -s -X POST http://localhost:8005/api/v1/mcp/function \
  -H "Content-Type: application/json" \
  -d '{"function": "get_agent_status", "arguments": {}}'

echo -e "\n\nDone." 