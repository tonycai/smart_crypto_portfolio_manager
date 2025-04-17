# Smart Crypto Portfolio Manager - Acceptance Criteria

## 1. Market Analysis Agent

### Market Analysis Capability

**Scenario 1.1: Analyzing Market Trends for a Cryptocurrency Pair**

**Given** the Market Analysis Agent is running and connected to cryptocurrency exchanges  
**When** a user or another agent requests market analysis for a specific crypto pair (e.g., BTC/USD) and timeframe (e.g., 1h)  
**Then** the agent should analyze the market data and return a response containing:
- A market trend classification (bullish, bearish, or neutral)
- A confidence level between 0 and 1
- A list of identified trading signals with their types and strengths

**Scenario 1.2: Handling Invalid Market Analysis Requests**

**Given** the Market Analysis Agent is running  
**When** a request is made with missing required parameters (crypto_pair or timeframe)  
**Then** the agent should return an appropriate error message and not perform the analysis

### Risk Assessment Capability

**Scenario 1.3: Initial Risk Assessment for a Potential Trade**

**Given** the Market Analysis Agent is running  
**When** a user or another agent requests risk assessment for a potential trade with crypto_pair and position_size  
**Then** the agent should perform a risk assessment and return:
- A risk level classification (low, medium, high, or extreme)
- A recommendation based on the risk assessment

### Market Monitoring

**Scenario 1.4: Detecting Trading Opportunities During Market Monitoring**

**Given** the Market Analysis Agent is running and configured to monitor specific cryptocurrency pairs  
**When** the agent detects a strong trading signal during its continuous monitoring  
**Then** it should log the detection and prepare to notify other agents about the opportunity

## 2. Trade Execution Agent

### Trade Execution Capability

**Scenario 2.1: Executing a Buy Order on a Cryptocurrency Exchange**

**Given** the Trade Execution Agent is running and authenticated with a cryptocurrency exchange  
**When** it receives a valid execute_trade task with:
- exchange = "binance"
- crypto_pair = "BTC/USD"
- action = "buy"
- order_type = "limit"
- quantity = 0.5
- price = 50000  
**Then** it should execute the order on the specified exchange and return:
- A unique order_id
- The order status
- The executed price
- The executed quantity
- A timestamp of the execution

**Scenario 2.2: Handling Trade Execution Errors**

**Given** the Trade Execution Agent is running  
**When** it receives a trade execution request with invalid parameters or for an exchange that's not accessible  
**Then** it should return an appropriate error message and not execute the trade

### Order Status Retrieval

**Scenario 2.3: Retrieving Status of an Existing Order**

**Given** the Trade Execution Agent is running and has access to a cryptocurrency exchange  
**When** it receives a get_order_status request with a valid exchange and order_id  
**Then** it should return the current status of the order, including:
- The order status (filled, partially_filled, open, canceled, or rejected)
- The executed price (if applicable)
- The executed quantity (if applicable)
- The remaining quantity to be executed (if applicable)

## 3. Risk Management Agent

### Trade Risk Assessment

**Scenario 3.1: Assessing Risk for a Proposed Trade**

**Given** the Risk Management Agent is running with access to portfolio data  
**When** it receives an assess_trade_risk request with:
- crypto_pair = "ETH/USD"
- action = "buy"
- quantity = 10
- price = 3000  
**Then** it should calculate the risk impact and return:
- A risk score between 0 and 100
- An approval boolean (true/false)
- The maximum recommended quantity to maintain acceptable risk levels
- A list of reasons explaining the risk assessment

### Portfolio Risk Monitoring

**Scenario 3.2: Monitoring Overall Portfolio Risk**

**Given** the Risk Management Agent is running with access to portfolio data  
**When** it receives a monitor_portfolio_risk request with specific metrics to analyze  
**Then** it should evaluate the portfolio risk and return:
- The overall risk level (low, medium, high, or extreme)
- The calculated values for the requested risk metrics
- Any alerts for metrics that exceed their thresholds, including recommendations

**Scenario 3.3: Automatic Risk Mitigation for High-Risk Situations**

**Given** the Risk Management Agent is running and monitoring portfolio risk  
**When** it detects that the overall portfolio risk level has reached 'high' or 'extreme'  
**Then** it should automatically initiate risk mitigation actions by:
- Creating tasks for the Trade Execution Agent to reduce high-risk positions
- Logging the detection and actions taken
- Sending notifications to relevant systems/users

## 4. Reporting and Analytics Agent

### Performance Report Generation

**Scenario 4.1: Generating a Performance Report**

**Given** the Reporting and Analytics Agent is running with access to portfolio and trading data  
**When** it receives a generate_performance_report request with:
- time_period = "month"
- format = "json"
- include_metrics = ["total_return", "sharpe_ratio", "drawdowns"]  
**Then** it should generate a comprehensive performance report and return:
- A unique report_id
- A summary of key performance metrics
- A URL to access the full report
- The complete report data (for JSON format)

### Portfolio Valuation

**Scenario 4.2: Generating a Portfolio Valuation Report**

**Given** the Reporting and Analytics Agent is running with access to cryptocurrency price data  
**When** it receives a generate_portfolio_valuation request with format = "json"  
**Then** it should calculate the current portfolio value and return:
- The total portfolio value
- The currency of valuation
- The timestamp of the valuation
- A breakdown of each asset in the portfolio (if include_details is true)
- A URL to access the full report

## 5. Agent-to-Agent Communication

### Agent Discovery

**Scenario 5.1: Discovering Agent Capabilities**

**Given** all agents are running and exposing their agent.json files  
**When** an agent needs to discover the capabilities of another agent  
**Then** it should be able to retrieve the agent card via the discovery endpoint and:
- Correctly parse the agent's capabilities
- Store the information for future reference
- Use it to form valid requests to that agent

### Task Creation and Management

**Scenario 5.2: Creating and Tracking a Task Between Agents**

**Given** the Market Analysis Agent has identified a trading opportunity  
**When** it creates a task for the Risk Management Agent to assess trade risk  
**Then** the task should be:
- Assigned a unique task_id
- Properly routed to the Risk Management Agent
- Processed according to its priority
- Updated with status changes (pending → in_progress → completed)
- Returned with appropriate results

### Multi-Agent Workflow

**Scenario 5.3: Executing a Complete Trading Workflow Across Multiple Agents**

**Given** all agents are running and able to communicate with each other  
**When** the Market Analysis Agent identifies a buy signal for ETH/USDT  
**Then** a complete workflow should execute successfully where:
1. The Market Analysis Agent requests risk assessment from the Risk Management Agent
2. The Risk Management Agent evaluates and approves the trade
3. The Market Analysis Agent sends a trade execution request to the Trade Execution Agent
4. The Trade Execution Agent executes the trade and confirms completion
5. The Trade Execution Agent notifies the Reporting and Analytics Agent about the trade
6. The Reporting and Analytics Agent updates its data to include the new trade

## 6. Deployment and Operations

### Docker Containerization

**Scenario 6.1: Deploying the System with Docker Compose**

**Given** the Docker and Docker Compose are installed on the host machine  
**When** a user runs 'docker-compose up' in the project directory  
**Then** all agent containers should:
- Build successfully from their respective Dockerfiles
- Start and bind to their configured ports
- Connect to the same a2a-network
- Access their configuration files from the mounted volumes
- Log their startup and operations at the configured log level

### Configuration Management

**Scenario 6.2: Applying Configuration Changes**

**Given** the system is running with Docker Compose  
**When** a user modifies a configuration file for an agent  
**Then** the agent should:
- Detect the configuration change (upon restart or reload)
- Apply the new configuration parameters
- Log that the configuration has been updated
- Continue operation with the new settings

### System Resilience

**Scenario 6.3: Handling Agent Failure and Recovery**

**Given** all agents are running in Docker containers  
**When** one agent container crashes or is stopped  
**Then** the following should occur:
- The Docker restart policy should automatically restart the failed container
- Other agents should handle the temporary unavailability gracefully
- When the agent recovers, it should resume processing tasks
- No data or task state should be lost during the recovery process

## 7. Orchestration Agent and MCP Protocol

### Agent Status Monitoring

**Scenario 7.1: Monitoring Status of All Agents**

**Given** the Orchestration Agent is running and connected to the network  
**When** a user or external system requests the status of all agents  
**Then** the Orchestration Agent should:
- Return the operational status of each agent (active, inactive, error)
- Include the last heartbeat timestamp for each agent
- Provide a summary of the overall system health

### Workflow Execution

**Scenario 7.2: Executing a Predefined Workflow**

**Given** the Orchestration Agent is running with defined workflows  
**When** it receives a request to execute a workflow named "market_analysis_and_trade"  
**Then** the agent should:
- Create and manage all necessary tasks across appropriate agents
- Track the progress of the workflow
- Return a unique workflow_id
- Allow the workflow status to be queried using this ID

### MCP Protocol Function Calls

**Scenario 7.3: Handling Function Call via MCP Protocol**

**Given** the Orchestration Agent is running with MCP protocol enabled  
**When** an external LLM makes a function call via HTTP to `/api/v1/mcp/function` with:
```json
{
  "function_name": "get_agent_status",
  "arguments": {}
}
```
**Then** the agent should:
- Process the request according to MCP protocol
- Return a properly formatted JSON response with the status of all agents
- Include appropriate HTTP status codes for success or error cases

**Scenario 7.4: Executing Complex Functions via MCP**

**Given** the Orchestration Agent is running with MCP protocol enabled  
**When** an external LLM makes a function call to analyze a trading opportunity:
```json
{
  "function_name": "analyze_trading_opportunity",
  "arguments": {
    "crypto_pair": "BTC/USD",
    "timeframe": "4h"
  }
}
```
**Then** the agent should:
- Coordinate with the Market Analysis Agent to perform the analysis
- Return the results in the format specified by the MCP protocol
- Include any error handling information if the analysis fails

### Workflow Status Tracking

**Scenario 7.5: Tracking Workflow Execution Status**

**Given** the Orchestration Agent has initiated a workflow  
**When** a user or system requests the status of that workflow using its ID  
**Then** the agent should return:
- The current status of the workflow (pending, in_progress, completed, failed)
- A list of completed steps and their results
- A list of pending steps
- Any errors encountered during execution
- The estimated time to completion (if available)
