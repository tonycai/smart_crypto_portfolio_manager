#!/usr/bin/env python3
"""
Orchestration Agent for Smart Crypto Portfolio Manager

This agent manages and coordinates the other agents in the system,
monitors their status, and provides an interface for LLM function calls via MCP protocol.
"""

import os
import sys
import json
import uuid
import asyncio
import logging
import requests
import uvicorn
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import traceback

# Import A2A server and client
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from a2a.server import A2AServer
from a2a.client import A2AClient


class OrchestrationAgent:
    """Orchestration Agent for Smart Crypto Portfolio Manager."""
    
    def __init__(self, config_path: str = None):
        """
        Initialize the Orchestration Agent.
        
        Args:
            config_path: Path to the configuration file
        """
        self.name = "Orchestration Agent"
        self.version = "1.0.0"
        
        # Set up logging
        self.logger = logging.getLogger(self.name)
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Set up A2A server
        agent_card_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent.json")
        self.a2a_server = A2AServer(agent_card_path)
        
        # Register capability handlers
        self.a2a_server.register_capability_handler("get_agent_status", self.get_agent_status)
        self.a2a_server.register_capability_handler("execute_workflow", self.execute_workflow)
        self.a2a_server.register_capability_handler("execute_llm_function", self.execute_llm_function)
        self.a2a_server.register_capability_handler("get_workflow_status", self.get_workflow_status)
        
        # Set up A2A client for communicating with other agents
        self.a2a_client = A2AClient(self.name, self.version)
        
        # Store agent configurations
        self.agent_configs = {
            "Market Analysis Agent": {
                "url": self.config.get("market_analysis_agent_url", "http://localhost:8001"),
                "port": 8001
            },
            "Trade Execution Agent": {
                "url": self.config.get("trade_execution_agent_url", "http://localhost:8002"),
                "port": 8002
            },
            "Risk Management Agent": {
                "url": self.config.get("risk_management_agent_url", "http://localhost:8003"),
                "port": 8003
            },
            "Reporting and Analytics Agent": {
                "url": self.config.get("reporting_analytics_agent_url", "http://localhost:8004"),
                "port": 8004
            }
        }
        
        # Store active workflows
        self.workflows = {}
        
        # MCP Protocol Functions
        self.mcp_functions = {
            "get_agent_status": self._mcp_get_agent_status,
            "execute_market_analysis": self._mcp_execute_market_analysis,
            "execute_trade": self._mcp_execute_trade,
            "assess_risk": self._mcp_assess_risk,
            "generate_report": self._mcp_generate_report,
            "execute_workflow": self._mcp_execute_workflow
        }
    
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """
        Load configuration from a file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Configuration as a dictionary
        """
        default_config = {
            "market_analysis_agent_url": "http://market-analysis-agent:8001",
            "trade_execution_agent_url": "http://trade-execution-agent:8002",
            "risk_management_agent_url": "http://risk-management-agent:8003",
            "reporting_analytics_agent_url": "http://reporting-analytics-agent:8004",
            "workflows": {
                "market_analysis_to_trade": {
                    "steps": [
                        {"agent": "Market Analysis Agent", "capability": "market_analysis"},
                        {"agent": "Risk Management Agent", "capability": "assess_trade_risk"},
                        {"agent": "Trade Execution Agent", "capability": "execute_trade"}
                    ]
                },
                "risk_assessment": {
                    "steps": [
                        {"agent": "Risk Management Agent", "capability": "monitor_portfolio_risk"}
                    ]
                },
                "performance_report": {
                    "steps": [
                        {"agent": "Reporting and Analytics Agent", "capability": "generate_performance_report"}
                    ]
                },
                "portfolio_rebalance": {
                    "steps": [
                        {"agent": "Risk Management Agent", "capability": "monitor_portfolio_risk"},
                        {"agent": "Market Analysis Agent", "capability": "market_analysis"},
                        {"agent": "Trade Execution Agent", "capability": "execute_trade"}
                    ]
                }
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    return {**default_config, **config}
            except Exception as e:
                self.logger.error(f"Error loading configuration from {config_path}: {e}")
        
        return default_config
    
    async def _discover_agents(self):
        """Discover all agents in the system."""
        for agent_name, agent_config in self.agent_configs.items():
            try:
                self.logger.info(f"Discovering agent: {agent_name} at {agent_config['url']}")
                agent_card = self.a2a_client.discover_agent(agent_config['url'])
                self.logger.info(f"Discovered agent: {agent_name} with {len(agent_card.get('capabilities', []))} capabilities")
            except Exception as e:
                self.logger.error(f"Failed to discover agent {agent_name}: {e}")
    
    async def get_agent_status(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the status of all agents or a specific agent.
        
        Args:
            parameters: Parameters for the capability, may include 'agent_name'
            
        Returns:
            Status information for the requested agent(s)
        """
        agent_name = parameters.get("agent_name")
        
        if agent_name and agent_name not in self.agent_configs:
            return {
                "error": f"Agent '{agent_name}' not found",
                "status": "error"
            }
        
        result = {"status": {}}
        
        agents_to_check = [agent_name] if agent_name else self.agent_configs.keys()
        
        for name in agents_to_check:
            agent_config = self.agent_configs.get(name)
            if not agent_config:
                continue
            
            try:
                # Check if the agent is up by making a request to its health endpoint
                response = requests.get(f"{agent_config['url']}", timeout=5)
                
                if response.status_code == 200:
                    # Get more detailed info from the agent card
                    try:
                        agent_card = self.a2a_client.discover_agent(agent_config['url'])
                        capabilities = [cap["name"] for cap in agent_card.get("capabilities", [])]
                        
                        result["status"][name] = {
                            "status": "online",
                            "version": agent_card.get("version", "unknown"),
                            "capabilities": capabilities,
                            "url": agent_config['url']
                        }
                    except Exception:
                        # If agent card discovery fails, just mark as online
                        result["status"][name] = {
                            "status": "online",
                            "url": agent_config['url']
                        }
                else:
                    result["status"][name] = {
                        "status": "error",
                        "message": f"Agent returned status code {response.status_code}",
                        "url": agent_config['url']
                    }
            except requests.RequestException:
                result["status"][name] = {
                    "status": "offline",
                    "url": agent_config['url']
                }
        
        return result
    
    async def execute_workflow(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a predefined workflow across multiple agents.
        
        Args:
            parameters: Parameters for the workflow
            
        Returns:
            Workflow execution status
        """
        workflow_name = parameters.get("workflow_name")
        workflow_params = parameters.get("parameters", {})
        
        if not workflow_name:
            return {"error": "Workflow name is required", "status": "error"}
        
        if workflow_name not in self.config.get("workflows", {}):
            return {"error": f"Workflow '{workflow_name}' not found", "status": "error"}
        
        # Create a workflow instance
        workflow_id = str(uuid.uuid4())
        workflow = {
            "id": workflow_id,
            "name": workflow_name,
            "status": "in_progress",
            "steps": [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "parameters": workflow_params,
            "result": None
        }
        
        # Store the workflow
        self.workflows[workflow_id] = workflow
        
        # Execute the workflow asynchronously
        asyncio.create_task(self._execute_workflow_steps(workflow_id, workflow_name, workflow_params))
        
        return {
            "workflow_id": workflow_id,
            "status": "in_progress"
        }
    
    async def _execute_workflow_steps(self, workflow_id: str, workflow_name: str, workflow_params: Dict[str, Any]):
        """
        Execute the steps of a workflow.
        
        Args:
            workflow_id: ID of the workflow
            workflow_name: Name of the workflow
            workflow_params: Parameters for the workflow
        """
        workflow = self.workflows[workflow_id]
        workflow_steps = self.config["workflows"][workflow_name]["steps"]
        
        try:
            step_results = {}
            
            for i, step in enumerate(workflow_steps):
                agent_name = step["agent"]
                capability = step["capability"]
                
                # Prepare parameters for this step
                step_params = workflow_params.copy()
                
                # Update parameters based on previous steps
                for prev_step, prev_result in step_results.items():
                    # In a real implementation, you would have a mapping of how results flow between steps
                    # For simplicity, we're just copying all previous results into the parameters
                    step_params[f"{prev_step}_result"] = prev_result
                
                # Execute the step
                self.logger.info(f"Executing workflow step {i+1}/{len(workflow_steps)}: {agent_name}.{capability}")
                
                workflow["steps"].append({
                    "step_id": i+1,
                    "agent": agent_name,
                    "capability": capability,
                    "status": "in_progress",
                    "parameters": step_params
                })
                
                workflow["updated_at"] = datetime.utcnow().isoformat()
                
                try:
                    # Discover the agent if not already discovered
                    if agent_name not in self.a2a_client.agent_registry:
                        agent_url = self.agent_configs[agent_name]["url"]
                        self.a2a_client.discover_agent(agent_url)
                    
                    # Create a task for the agent
                    task = self.a2a_client.create_task(
                        agent_name=agent_name,
                        capability=capability,
                        parameters=step_params
                    )
                    
                    # Wait for the task to complete
                    task_id = task["task_id"]
                    while True:
                        task_status = self.a2a_client.get_task(agent_name, task_id)
                        if task_status["status"] in ["completed", "failed"]:
                            break
                        await asyncio.sleep(1)
                    
                    if task_status["status"] == "completed":
                        step_result = task_status.get("result", {})
                        step_results[f"{capability}"] = step_result
                        
                        workflow["steps"][-1]["status"] = "completed"
                        workflow["steps"][-1]["result"] = step_result
                    else:
                        error = task_status.get("error", {"message": "Unknown error"})
                        workflow["steps"][-1]["status"] = "failed"
                        workflow["steps"][-1]["error"] = error
                        
                        # Fail the workflow if a step fails
                        workflow["status"] = "failed"
                        workflow["error"] = {
                            "message": f"Workflow step {i+1} failed",
                            "step": i+1,
                            "error": error
                        }
                        workflow["updated_at"] = datetime.utcnow().isoformat()
                        return
                    
                except Exception as e:
                    self.logger.error(f"Error executing workflow step: {e}")
                    traceback.print_exc()
                    
                    workflow["steps"][-1]["status"] = "failed"
                    workflow["steps"][-1]["error"] = {
                        "message": str(e)
                    }
                    
                    # Fail the workflow if a step fails
                    workflow["status"] = "failed"
                    workflow["error"] = {
                        "message": f"Workflow step {i+1} failed",
                        "step": i+1,
                        "error": {
                            "message": str(e)
                        }
                    }
                    workflow["updated_at"] = datetime.utcnow().isoformat()
                    return
            
            # All steps completed successfully
            workflow["status"] = "completed"
            workflow["result"] = step_results
            workflow["updated_at"] = datetime.utcnow().isoformat()
            
        except Exception as e:
            self.logger.error(f"Error executing workflow: {e}")
            traceback.print_exc()
            
            workflow["status"] = "failed"
            workflow["error"] = {
                "message": str(e)
            }
            workflow["updated_at"] = datetime.utcnow().isoformat()
    
    async def execute_llm_function(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a function requested by an LLM via MCP protocol.
        
        Args:
            parameters: Parameters for the function
            
        Returns:
            Result of the function execution
        """
        function_name = parameters.get("function_name")
        arguments = parameters.get("arguments", {})
        
        if not function_name:
            return {"error": "Function name is required", "status": "error"}
        
        if function_name not in self.mcp_functions:
            return {
                "error": f"Function '{function_name}' not found",
                "available_functions": list(self.mcp_functions.keys()),
                "status": "error"
            }
        
        try:
            # Execute the MCP function
            result = await self.mcp_functions[function_name](arguments)
            return result
        except Exception as e:
            self.logger.error(f"Error executing MCP function '{function_name}': {e}")
            traceback.print_exc()
            return {"error": str(e), "status": "error"}
    
    async def get_workflow_status(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the status of a workflow.
        
        Args:
            parameters: Parameters including the workflow_id
            
        Returns:
            Status of the workflow
        """
        workflow_id = parameters.get("workflow_id")
        
        if not workflow_id:
            return {"error": "Workflow ID is required", "status": "error"}
        
        if workflow_id not in self.workflows:
            return {"error": f"Workflow '{workflow_id}' not found", "status": "error"}
        
        workflow = self.workflows[workflow_id]
        
        return {
            "workflow_id": workflow_id,
            "name": workflow.get("name"),
            "status": workflow.get("status"),
            "created_at": workflow.get("created_at"),
            "updated_at": workflow.get("updated_at"),
            "steps": workflow.get("steps", []),
            "result": workflow.get("result")
        }
    
    # MCP Protocol Function Implementations
    
    async def _mcp_get_agent_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """MCP function to get agent status."""
        return await self.get_agent_status(arguments)
    
    async def _mcp_execute_market_analysis(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """MCP function to execute market analysis."""
        agent_name = "Market Analysis Agent"
        
        # Ensure the agent is discovered
        if agent_name not in self.a2a_client.agent_registry:
            agent_url = self.agent_configs[agent_name]["url"]
            try:
                self.a2a_client.discover_agent(agent_url)
            except Exception as e:
                return {"error": f"Failed to discover {agent_name}: {e}", "status": "error"}
        
        try:
            # Create a task for market analysis
            task = self.a2a_client.create_task(
                agent_name=agent_name,
                capability="market_analysis",
                parameters=arguments
            )
            
            # Return the task details
            return {
                "task_id": task["task_id"],
                "status": task["status"],
                "message": f"Market analysis task created successfully"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    async def _mcp_execute_trade(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """MCP function to execute a trade."""
        agent_name = "Trade Execution Agent"
        
        # Ensure the agent is discovered
        if agent_name not in self.a2a_client.agent_registry:
            agent_url = self.agent_configs[agent_name]["url"]
            try:
                self.a2a_client.discover_agent(agent_url)
            except Exception as e:
                return {"error": f"Failed to discover {agent_name}: {e}", "status": "error"}
        
        try:
            # Create a task for trade execution
            task = self.a2a_client.create_task(
                agent_name=agent_name,
                capability="execute_trade",
                parameters=arguments
            )
            
            # Return the task details
            return {
                "task_id": task["task_id"],
                "status": task["status"],
                "message": f"Trade execution task created successfully"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    async def _mcp_assess_risk(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """MCP function to assess risk."""
        agent_name = "Risk Management Agent"
        
        # Ensure the agent is discovered
        if agent_name not in self.a2a_client.agent_registry:
            agent_url = self.agent_configs[agent_name]["url"]
            try:
                self.a2a_client.discover_agent(agent_url)
            except Exception as e:
                return {"error": f"Failed to discover {agent_name}: {e}", "status": "error"}
        
        try:
            # Create a task for risk assessment
            task = self.a2a_client.create_task(
                agent_name=agent_name,
                capability="assess_trade_risk" if "crypto_pair" in arguments else "monitor_portfolio_risk",
                parameters=arguments
            )
            
            # Return the task details
            return {
                "task_id": task["task_id"],
                "status": task["status"],
                "message": f"Risk assessment task created successfully"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    async def _mcp_generate_report(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """MCP function to generate a report."""
        agent_name = "Reporting and Analytics Agent"
        
        # Ensure the agent is discovered
        if agent_name not in self.a2a_client.agent_registry:
            agent_url = self.agent_configs[agent_name]["url"]
            try:
                self.a2a_client.discover_agent(agent_url)
            except Exception as e:
                return {"error": f"Failed to discover {agent_name}: {e}", "status": "error"}
        
        try:
            # Determine the capability based on arguments
            if "time_period" in arguments:
                capability = "generate_performance_report"
            else:
                capability = "generate_portfolio_valuation"
            
            # Create a task for report generation
            task = self.a2a_client.create_task(
                agent_name=agent_name,
                capability=capability,
                parameters=arguments
            )
            
            # Return the task details
            return {
                "task_id": task["task_id"],
                "status": task["status"],
                "message": f"Report generation task created successfully"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    async def _mcp_execute_workflow(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """MCP function to execute a workflow."""
        return await self.execute_workflow(arguments)
    
    async def start(self, host: str = "0.0.0.0", port: int = 8005):
        """
        Start the Orchestration Agent.
        
        Args:
            host: Host to bind the server to
            port: Port to bind the server to
        """
        app = self.a2a_server.app
        
        # Add root endpoint for health checks
        @app.get("/")
        async def root():
            return {"status": "ok", "agent": self.name, "version": self.version}
        
        # Add MCP endpoint for LLM function calls
        @app.post("/api/v1/mcp/function")
        async def mcp_function(request_data: Dict[str, Any]):
            function_name = request_data.get("function")
            arguments = request_data.get("arguments", {})
            
            if not function_name:
                return {"error": "Function name is required", "status": "error"}
            
            parameters = {
                "function_name": function_name,
                "arguments": arguments
            }
            
            result = await self.execute_llm_function(parameters)
            return result
        
        # Discover other agents
        await self._discover_agents()
        
        self.logger.info(f"Starting Orchestration Agent on {host}:{port}")
        
        # Start the server properly in async context
        config = uvicorn.Config(app, host=host, port=port)
        server = uvicorn.Server(config)
        await server.serve()


async def main():
    """Main entry point for the Orchestration Agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Start the Orchestration Agent')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind the server to')
    parser.add_argument('--port', type=int, default=8005, help='Port to bind the server to')
    parser.add_argument('--config', help='Path to the configuration file')
    parser.add_argument('--log-level', default='INFO', 
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Logging level')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start the agent
    agent = OrchestrationAgent(config_path=args.config)
    await agent.start(host=args.host, port=args.port)


if __name__ == "__main__":
    asyncio.run(main()) 