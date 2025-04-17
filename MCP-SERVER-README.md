# Running the MCP Server in Docker

This guide explains how to run the MCP (Model Calling Protocol) server in Docker.

## Prerequisites

- Docker and Docker Compose installed on your system
- Basic knowledge of Docker commands

## Getting Started

1. Build and start the MCP server container:

```bash
docker-compose -f docker-compose-mcp.yml up --build
```

2. The server will be available at http://localhost:8000

3. To run in detached mode (in the background):

```bash
docker-compose -f docker-compose-mcp.yml up -d
```

4. To stop the server:

```bash
docker-compose -f docker-compose-mcp.yml down
```

## MCP Client Examples

The file `mcp-client-examples.json` contains example requests that can be made to the MCP server. Here's a basic example:

```bash
# Get status of all agents
curl -X POST http://localhost:8000/api/v1/mcp/function \
  -H "Content-Type: application/json" \
  -d '{"function_name": "get_all_agents_status", "arguments": {}}'
```

## API Endpoints

The MCP server provides the following endpoints:

- **POST /api/v1/mcp/function** - Call a function via the MCP protocol
- **GET /api/v1/mcp/status/agents** - Get status of all agents
- **GET /api/v1/mcp/status/agent/{agent_id}** - Get status of a specific agent
- **POST /api/v1/mcp/agent/register** - Register a new agent
- **POST /api/v1/mcp/workflow** - Create and execute a new workflow
- **GET /api/v1/mcp/workflow/{workflow_id}** - Get status of a specific workflow

## Troubleshooting

- If you encounter port conflicts, modify the port mapping in the `docker-compose-mcp.yml` file
- Check logs with `docker-compose -f docker-compose-mcp.yml logs`
- For real-time logs, use `docker-compose -f docker-compose-mcp.yml logs -f` 