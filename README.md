# Smart Crypto Portfolio Manager

A sophisticated multi-agent system for intelligent cryptocurrency portfolio management using the Agent-to-Agent (A2A) communication protocol.

## Overview

The Smart Crypto Portfolio Manager is a modular and extensible system that leverages multiple specialized AI agents to automate and optimize cryptocurrency trading. Each agent focuses on a specific aspect of trading, and they communicate with each other through a standardized A2A protocol, implementing [Google's open Agent-to-Agent (A2A) protocol](https://github.com/google/A2A) for seamless interoperability with other agent systems.

## System Architecture



The system consists of five main agents:

1. **Market Analysis Agent**: Monitors crypto markets, analyzes trends, and identifies trading opportunities.
2. **Trade Execution Agent**: Executes buy/sell orders on various crypto exchanges.
3. **Risk Management Agent**: Monitors portfolio risk exposure and suggests risk mitigation actions.
4. **Reporting and Analytics Agent**: Generates reports on trading performance and portfolio valuation.
5. **Orchestration Agent**: Manages the coordination of all agents, provides status monitoring, and accepts LLM function calls via the MCP protocol.

### Agent Communication

Agents communicate using two protocols:

#### Agent-to-Agent (A2A) Protocol
- Implements the [Google Agent-to-Agent (A2A) protocol](https://github.com/google/A2A) for standardized agent communication
- Agent discovery through agent cards (JSON files describing capabilities)
- Task-based interaction model
- Structured JSON messages
- Secure and reliable communication

#### Machine-Callable Protocol (MCP)
- The Orchestration Agent implements the MCP protocol for LLM function calls
- Allows external AI systems to interact with the platform
- Structured JSON schemas for function definitions
- Streamlined function calling interface

## A2A Protocol Integration

This project fully implements Google's [Agent-to-Agent (A2A) protocol](https://github.com/google/A2A), allowing our agents to communicate not only with each other but also with any other A2A-compatible agents in the ecosystem. This integration provides several benefits:

### A2A Features Implemented

- **Agent Card:** Our system exposes a standard Agent Card at `/.well-known/agent.json` describing all agent capabilities
- **Task-Based API:** All agent interactions follow the A2A task lifecycle (submitted, working, input-required, completed, failed, canceled)
- **Streaming Support:** Real-time task updates via Server-Sent Events (SSE)
- **Push Notifications:** Proactive updates to client applications
- **Skills Framework:** Standardized skill definitions for all agent capabilities

### Interoperability Benefits

- Connect with agents built on other frameworks (CrewAI, LangGraph, Semantic Kernel, etc.)
- Extend capabilities through third-party A2A agents
- Future-proof design aligned with emerging industry standards
- Simplified integration with LLM-based systems

### A2A Agent Ecosystem

Our implementation is compatible with the growing ecosystem of A2A-enabled agents and frameworks, including:

- Agent Development Kit (ADK)
- CrewAI
- LangGraph
- Genkit
- LlamaIndex
- Semantic Kernel

For more information on the A2A protocol, visit the [official GitHub repository](https://github.com/google/A2A).

## Use Cases

### Automated Trading Strategy Execution

The Market Analysis Agent continuously monitors crypto markets and identifies trading opportunities based on technical analysis, trend detection, and pattern recognition. When it identifies a potential trade, it:

1. Requests a risk assessment from the Risk Management Agent
2. If the risk is acceptable, sends a trade execution request to the Trade Execution Agent
3. Notifies the Reporting and Analytics Agent about the trade
4. Monitors the trade and adjusts strategy as needed

### Risk Management and Portfolio Optimization

The Risk Management Agent continuously evaluates the overall portfolio risk and can:

1. Set stop-loss and take-profit levels for active positions
2. Recommend portfolio rebalancing when asset allocations drift
3. Trigger emergency protocols during market crashes
4. Impose limits on trade sizes based on risk metrics

### Performance Tracking and Reporting

The Reporting and Analytics Agent automatically generates reports on:

1. Daily, weekly, and monthly trading performance
2. Portfolio valuation and asset allocation
3. Risk metrics and exposure analysis
4. Trade statistics and execution quality

### Workflow Orchestration and System Monitoring

The Orchestration Agent provides centralized control and monitoring:

1. Executes predefined workflows across multiple agents
2. Monitors the status of all agents in the system
3. Provides a unified interface for LLM function calls via MCP
4. Tracks workflow execution progress

### LLM Integration via MCP Protocol

External AI systems can interact with the platform through the MCP protocol:

1. Query agent status and system health
2. Execute market analysis and trades
3. Assess portfolio risk
4. Generate performance reports
5. Execute multi-agent workflows

## Setup and Installation

### Prerequisites

- Docker and Docker Compose
- Python 3.9+
- API keys for cryptocurrency exchanges (Binance, Coinbase, etc.)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/tonycai/smart_crypto_portfolio_manager.git
   cd smart_crypto_portfolio_manager
   ```

2. Configure the system:
   - Edit the configuration files in the `config/` directory
   - Set your API keys in `config/trade_execution.json`
   - Adjust risk parameters in `config/risk_management.json`
   - Configure MCP functions in `config/orchestration.json`

3. Build and start the containers:
   ```bash
   docker-compose build
   docker-compose up -d
   ```

## Docker Deployment

Each agent runs in its own Docker container, making deployment and scaling easy:

### Container Configuration

- **Market Analysis Agent**: Runs on port 8001
- **Trade Execution Agent**: Runs on port 8002
- **Risk Management Agent**: Runs on port 8003
- **Reporting and Analytics Agent**: Runs on port 8004
- **Orchestration Agent**: Runs on port 8005

### Scaling

You can scale individual agents to handle higher loads:

```bash
docker-compose up -d --scale market-analysis-agent=3
```

### Monitoring

Monitor the system using standard Docker commands:

```bash
docker-compose ps
docker-compose logs -f
```

## Development

### Project Structure

- `agents/`: Contains the implementation of each specialized agent
  - `market_analysis/`: Market Analysis Agent implementation
  - `trade_execution/`: Trade Execution Agent implementation
  - `risk_management/`: Risk Management Agent implementation
  - `reporting_analytics/`: Reporting and Analytics Agent implementation
  - `orchestration/`: Orchestration Agent implementation
- `a2a/`: Implementation of the Agent-to-Agent communication protocol
- `config/`: Configuration files for each agent
- `common/`: Shared utilities and code

### Adding New Agents

1. Create a new directory in `agents/`
2. Create an `agent.json` file defining the agent's capabilities
3. Implement the agent's functionality
4. Add the agent to `docker-compose.yml`

### Extending Agent Capabilities

1. Add new capability definitions to the agent's `agent.json` file
2. Implement the corresponding handler functions
3. Register the handlers in the agent's initialization

## API Documentation

Each agent exposes a RESTful API following the A2A protocol:

- **Agent Discovery**: `GET /api/v1/agent`
- **Task Management**:
  - Create Task: `POST /api/v1/tasks`
  - Get Task: `GET /api/v1/tasks/{task_id}`
  - Update Task: `PUT /api/v1/tasks/{task_id}`
  - Delete Task: `DELETE /api/v1/tasks/{task_id}`
- **Messaging**:
  - Send Message: `POST /api/v1/tasks/{task_id}/messages`
  - Get Messages: `GET /api/v1/tasks/{task_id}/messages`

The Orchestration Agent also implements the MCP protocol:

- **LLM Function Calls**: `POST /api/v1/mcp/function`

## Security Considerations

- API keys are stored in configuration files and never exposed in logs
- Communication between agents can be secured with TLS
- Authentication is required for task creation
- Risk limits prevent catastrophic trading errors

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Feedback and Support

Have suggestions or need help? Feel free to reach out:

- **Telegram**: [@tonyironreal](https://t.me/tonyironreal) - Send your feature requests or report issues
- **GitHub Issues**: For bug reports and feature requests

## Donations

If you find this project helpful and would like to support its development, you can donate cryptocurrency to the following addresses:

- **Solana (SOL)**: `ESUpLq9tCo1bmauWoN1rgNiYwwr5K587h15SrJz9L7ct` (Phantom Wallet)

Your support is greatly appreciated and helps maintain and improve this project!

## License

MIT License

Copyright (c) 2025 TonyCai

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Disclaimer

This software is for educational and research purposes only. Cryptocurrency trading involves significant risk. Use at your own risk.
