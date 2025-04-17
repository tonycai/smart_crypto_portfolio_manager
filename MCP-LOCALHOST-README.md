# Using MCP with Localhost Connections

This guide explains how to use the Model Calling Protocol (MCP) client to interact with the Smart Crypto Portfolio Manager's agents using localhost connections.

## Setup

1. **Update Agent Configuration**

   Update the orchestration agent to use localhost instead of container hostnames:

   ```bash
   python3 update_agent_config.py config/orchestration.json
   ```

   Or modify the agent code directly:

   ```bash
   python3 update_orchestration_agent.py agents/orchestration/agent.py
   ```

2. **Restart Containers**

   After updating configurations, restart the containers:

   ```bash
   ./restart_containers.sh
   ```

## Using the MCP Client

The Python MCP client provides a command-line interface for interacting with the system:

### View Agent Status

```bash
# Get status of all agents
python3 mcp_client.py --server http://localhost:8005 agents

# Get status of a specific agent
python3 mcp_client.py --server http://localhost:8005 agent "Trade Execution Agent"
```

### List Available Functions

```bash
python3 mcp_client.py --server http://localhost:8005 functions
```

### Call MCP Functions

```bash
# Execute market analysis
python3 mcp_client.py --server http://localhost:8005 function "execute_market_analysis" --args '{"crypto_pair": "BTC/USD", "timeframe": "4h"}'

# Execute a trade
python3 mcp_client.py --server http://localhost:8005 function "execute_trade" --args '{"crypto_pair": "BTC/USD", "action": "buy", "amount": 0.1}'

# Assess portfolio risk
python3 mcp_client.py --server http://localhost:8005 function "assess_risk" --args '{"portfolio": {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}}'

# Generate a report
python3 mcp_client.py --server http://localhost:8005 function "generate_report" --args '{"report_type": "performance", "timeframe": "1w"}'

# Execute a workflow
python3 mcp_client.py --server http://localhost:8005 function "execute_workflow" --args '{"workflow_name": "portfolio_rebalance", "parameters": {"risk_tolerance": "medium", "target_assets": ["BTC", "ETH", "SOL", "AVAX", "ADA"]}}'

# Check workflow status
python3 mcp_client.py --server http://localhost:8005 function "get_workflow_status" --args '{"workflow_id": "<WORKFLOW_ID>"}'
```

### Check Server Health

```bash
python3 mcp_client.py --server http://localhost:8005 health
```

## Using the Test Script

The test script makes it easy to try different functions:

```bash
./test_mcp_functions.sh
```

## Integration with Cursor IDE

1. Copy the MCP client configuration to Cursor:

   ```bash
   # For macOS
   cp mcp.json ~/Library/Application\ Support/Cursor/extensions/
   
   # For Linux
   cp mcp.json ~/.config/Cursor/extensions/
   
   # For Windows (in PowerShell)
   Copy-Item mcp.json -Destination "$env:APPDATA\Cursor\extensions\"
   ```

2. Restart Cursor IDE to load the configurations.

3. The MCP functions will be available in the Cursor command palette.

## Troubleshooting

1. **Connection Issues**

   If you get connection refused errors:
   - Make sure all containers are running: `docker-compose ps`
   - Check container logs: `docker logs <container_name>`
   - Ensure ports are correctly mapped in docker-compose.yml

2. **Market Analysis Agent Issues**

   If the Market Analysis Agent returns 404 errors:
   - Check its implementation: `cat agents/market_analysis/agent.py`
   - Verify it has a root endpoint (`/`) handler

3. **Function Execution Errors**

   If function calls return errors:
   - Ensure the arguments are correctly formatted
   - Check that the function exists: `python3 mcp_client.py --server http://localhost:8005 functions`
   - Verify agent connectivity: `python3 mcp_client.py --server http://localhost:8005 agents`

## MCP Function Reference

| Function | Description | Example Arguments |
|----------|-------------|-------------------|
| `get_agent_status` | Get status of agents | `{}` or `{"agent_name": "Trade Execution Agent"}` |
| `execute_market_analysis` | Run market analysis | `{"crypto_pair": "BTC/USD", "timeframe": "4h"}` |
| `execute_trade` | Execute a trade | `{"crypto_pair": "BTC/USD", "action": "buy", "amount": 0.1}` |
| `assess_risk` | Assess portfolio risk | `{"portfolio": {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}}` |
| `generate_report` | Generate a portfolio report | `{"report_type": "performance", "timeframe": "1w"}` |
| `execute_workflow` | Execute a workflow | `{"workflow_name": "portfolio_rebalance", "parameters": {...}}` |
| `get_workflow_status` | Check workflow status | `{"workflow_id": "<WORKFLOW_ID>"}` | 