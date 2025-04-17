== AI Agent ==

Top Row:

靈感: Inspiration
對談需求: Dialogue requirements / Interview needs
用戶故事: User story

Bottom Row:

驗收標準: Acceptance criteria
編寫程式: Write program / Code
測試程式: Test program / Test code

== AI Agent Workflow ==

# Traditional Workflow (Agent-to-Agent Protocol)

1. Market Analysis Agent identifies trading opportunity
2. Market Analysis Agent requests risk assessment from Risk Management Agent
3. Risk Management Agent provides risk assessment
4. Market Analysis Agent initiates trade with Trade Execution Agent if risk is acceptable
5. Trade Execution Agent executes trade and notifies Market Analysis Agent
6. Trade Execution Agent logs trade with Reporting and Analytics Agent
7. Reporting and Analytics Agent updates portfolio data

# Enhanced Workflow with Orchestration Agent

1. External LLM (e.g., Claude, GPT) analyzes market conditions
2. LLM calls Orchestration Agent using MCP protocol
3. Orchestration Agent executes predefined workflow:
   a. Requests market analysis from Market Analysis Agent
   b. Requests risk assessment from Risk Management Agent
   c. Initiates trade with Trade Execution Agent if appropriate
   d. Requests portfolio update from Reporting and Analytics Agent
4. Orchestration Agent tracks workflow status and reports back to LLM
5. LLM can make additional function calls as needed

# MCP Protocol Function Call Flow

1. External system makes HTTP request to `/api/v1/mcp/function`
2. Request contains function name and arguments in JSON format
3. Orchestration Agent validates and processes the request
4. Orchestration Agent communicates with appropriate specialized agents
5. Orchestration Agent returns result to the caller

# System Status Monitoring Flow

1. Orchestration Agent periodically checks status of all agents
2. Orchestration Agent maintains health status of all components
3. External systems can query agent status through MCP protocol
