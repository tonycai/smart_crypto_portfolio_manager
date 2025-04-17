"""
Modified version of the Orchestration Agent that supports different endpoints for different agents,
particularly setting up a separate endpoint for the Market Analysis Agent.
"""
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable
from enum import Enum
from dataclasses import dataclass, field
import importlib
import os
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("OrchestrationAgent")

class StepStatus(str, Enum):
    """Status of a workflow step"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    
class WorkflowStatus(str, Enum):
    """Status of an entire workflow"""
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"

class AgentStatus(str, Enum):
    """Status of an agent"""
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    ERROR = "ERROR"
    OFFLINE = "OFFLINE"

@dataclass
class Agent:
    """Representation of an MCP agent"""
    id: str
    name: str
    description: str
    functions: List[str]
    status: AgentStatus = AgentStatus.AVAILABLE
    last_active: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    endpoint: Optional[str] = None  # Added endpoint field for per-agent endpoints
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary representation"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "functions": self.functions,
            "status": self.status,
            "last_active": self.last_active.isoformat(),
            "metadata": self.metadata,
            "endpoint": self.endpoint
        }
    
    def update_status(self, status: AgentStatus) -> None:
        """Update the agent's status"""
        self.status = status
        self.last_active = datetime.now()

@dataclass
class WorkflowStep:
    """A single step in a workflow"""
    id: str
    name: str
    agent_id: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary representation"""
        return {
            "id": self.id,
            "name": self.name,
            "agent_id": self.agent_id,
            "parameters": self.parameters,
            "depends_on": self.depends_on,
            "status": self.status,
            "result": self.result,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

@dataclass
class Workflow:
    """A workflow composed of multiple steps"""
    name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    steps: List[WorkflowStep] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.CREATED
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    def add_step(self, step: WorkflowStep) -> None:
        """Add a step to the workflow"""
        self.steps.append(step)
    
    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get a step by its ID"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary representation"""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "steps": [step.to_dict() for step in self.steps],
            "context": self.context
        }

class OrchestrationAgent:
    """
    Agent responsible for managing other agents and orchestrating workflows.
    Implements the Model Calling Protocol (MCP) functionality.
    
    Key modifications:
    - Added agent_endpoints dictionary to configure specific endpoints for different agents
    - Updated register_agent to support custom endpoints per agent type
    - Updated execute_function to use the appropriate endpoint for each agent
    """
    
    def __init__(self):
        """Initialize the orchestration agent"""
        self.agents: Dict[str, Agent] = {}
        self.workflows: Dict[str, Workflow] = {}
        self.function_to_agent: Dict[str, str] = {}  # Maps function names to agent IDs
        self.workflow_lock = threading.Lock()
        self.execution_threads: Dict[str, threading.Thread] = {}
        
        # Initialize workflow modules registry
        self.workflow_modules: Dict[str, Any] = {}
        self.load_workflow_modules()
        
        # Agent endpoint configuration - NEW ADDITION
        self.agent_endpoints = {
            "market_analysis_agent": "/api/v1/agent",  # Special endpoint for market analysis
            "default": "/api/agent"  # Default endpoint for other agents
        }
        
        logger.info("Orchestration Agent initialized")
    
    def load_workflow_modules(self) -> None:
        """Load all workflow modules"""
        workflows_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workflows")
        if not os.path.exists(workflows_dir):
            logger.warning(f"Workflows directory not found: {workflows_dir}")
            return
            
        for filename in os.listdir(workflows_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = filename[:-3]  # Remove .py extension
                try:
                    # Adjust the import based on the project structure
                    module_path = f"src.workflows.{module_name}"
                    module = importlib.import_module(module_path)
                    if hasattr(module, "get_workflow"):
                        self.workflow_modules[module_name] = module
                        logger.info(f"Loaded workflow module: {module_name}")
                except Exception as e:
                    logger.error(f"Failed to load workflow module {module_name}: {str(e)}")
    
    def register_agent(self, agent_data: Dict[str, Any]) -> Agent:
        """
        Register a new agent with the orchestration system
        
        Args:
            agent_data: Dictionary containing agent information
            
        Returns:
            The registered Agent object
        """
        # Create agent object with endpoint configuration - MODIFIED
        agent_id = agent_data.get("id", str(uuid.uuid4()))
        agent_type = agent_data.get("type", "unknown")
        
        # Determine the endpoint based on agent ID, falling back to default
        endpoint = agent_data.get("endpoint")
        if endpoint is None:
            endpoint = self.agent_endpoints.get(agent_id, self.agent_endpoints["default"])
        
        agent = Agent(
            id=agent_id,
            name=agent_data.get("name", "Unknown Agent"),
            description=agent_data.get("description", ""),
            functions=agent_data.get("functions", []),
            metadata=agent_data.get("metadata", {}),
            endpoint=endpoint  # Store the endpoint in the agent
        )
        
        # Store agent
        self.agents[agent.id] = agent
        
        # Update function-to-agent mapping
        for function_name in agent.functions:
            self.function_to_agent[function_name] = agent.id
            
        logger.info(f"Registered agent: {agent.name} (ID: {agent.id}) with endpoint {endpoint}")
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID"""
        return self.agents.get(agent_id)
    
    def get_all_agents(self) -> List[Agent]:
        """Get all registered agents"""
        return list(self.agents.values())
    
    def get_agent_by_function(self, function_name: str) -> Optional[Agent]:
        """Find agent that implements a specific function"""
        agent_id = self.function_to_agent.get(function_name)
        if agent_id:
            return self.agents.get(agent_id)
        return None
    
    def execute_function(self, function_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a function by delegating to the appropriate agent
        
        Args:
            function_name: Name of the function to execute
            params: Parameters to pass to the function
            
        Returns:
            Result of the function execution
            
        Raises:
            ValueError: If no agent is found for the function or execution fails
        """
        agent = self.get_agent_by_function(function_name)
        if not agent:
            raise ValueError(f"No agent registered for function: {function_name}")
        
        # Update agent status
        agent.update_status(AgentStatus.BUSY)
        
        try:
            # Use the agent's custom endpoint or fall back to default - MODIFIED
            endpoint = agent.endpoint or self.agent_endpoints.get("default")
            
            # In a real implementation, this would communicate with the agent
            # using the appropriate endpoint
            logger.info(f"Executing function '{function_name}' on agent '{agent.id}' via endpoint {endpoint}")
            
            # Simulate agent processing
            time.sleep(0.2)
            
            # Generate demo result based on function name
            result = self._simulate_function_result(function_name, params)
            
            # Update agent status
            agent.update_status(AgentStatus.AVAILABLE)
            
            return {
                "status": "success",
                "result": result,
                "agent_id": agent.id
            }
            
        except Exception as e:
            # Update agent status to error
            agent.update_status(AgentStatus.ERROR)
            logger.error(f"Error executing function '{function_name}': {str(e)}")
            raise ValueError(f"Function execution failed: {str(e)}")
    
    def _simulate_function_result(self, function_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate result for demo purposes"""
        if function_name.startswith("fetch_"):
            return {"data": f"Mock data for {function_name}", "timestamp": datetime.now().isoformat()}
        elif function_name.startswith("analyze_"):
            return {"analysis_result": f"Mock analysis for {params}", "confidence": 0.85}
        elif function_name.startswith("generate_"):
            return {"strategy": "mock_strategy", "parameters": params}
        elif function_name.startswith("optimize_"):
            return {"allocation": {"BTC": 0.4, "ETH": 0.3, "SOL": 0.2, "Cash": 0.1}}
        elif function_name.startswith("prepare_"):
            return {"trades": [{"asset": "BTC", "action": "BUY", "amount": 0.1}]}
        else:
            return {"message": f"Executed {function_name} with {json.dumps(params)}"}

# Example usage
if __name__ == "__main__":
    # Initialize the orchestration agent
    orchestrator = OrchestrationAgent()
    
    # Register some agents
    orchestrator.register_agent({
        "id": "market_data_agent",
        "name": "Market Data Agent",
        "type": "market_data",
        "functions": ["fetch_market_data", "fetch_historical_prices"]
    })
    
    # Register market analysis agent with custom endpoint
    orchestrator.register_agent({
        "id": "market_analysis_agent",
        "name": "Market Analysis Agent",
        "type": "market_analysis",
        "functions": ["analyze_market_trends", "analyze_volatility"],
        "endpoint": "/api/v1/agent"  # Custom endpoint for this specific agent
    })
    
    # Test executing a function
    try:
        result = orchestrator.execute_function("analyze_market_trends", {"assets": ["BTC", "ETH"]})
        print(f"Function executed successfully: {json.dumps(result, indent=2)}")
    except ValueError as e:
        print(f"Error executing function: {str(e)}") 