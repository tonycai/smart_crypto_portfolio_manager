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
import sys

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
    endpoint: Optional[str] = None
    last_heartbeat: Optional[str] = None
    
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
            "endpoint": self.endpoint,
            "last_heartbeat": self.last_heartbeat
        }
    
    def update_status(self, status: AgentStatus) -> None:
        """Update the agent's status"""
        self.status = status
        self.last_active = datetime.now()
        self.last_heartbeat = datetime.now().isoformat()

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
    """
    
    def __init__(self):
        """Initialize the orchestration agent"""
        self.agents: Dict[str, Agent] = {}
        self.workflows: Dict[str, Workflow] = {}
        self.workflow_modules = {}
        self.function_to_agent: Dict[str, str] = {}  # Maps function names to agent IDs
        
        # Agent endpoint configuration
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
                    module_path = f"workflows.{module_name}"
                    module = importlib.import_module(module_path)
                    if hasattr(module, "get_workflow"):
                        self.workflow_modules[module_name] = module
                        logger.info(f"Loaded workflow module: {module_name}")
                except Exception as e:
                    logger.error(f"Failed to load workflow module {module_name}: {str(e)}")
    
    def register_agent(self, agent_id: str, agent_type: str) -> Dict[str, Any]:
        """Register a new agent in the system or update an existing one"""
        # Determine endpoint based on agent type
        endpoint = self.agent_endpoints.get(agent_id, self.agent_endpoints["default"])
        
        if agent_id in self.agents:
            self.agents[agent_id].update_heartbeat()
            logger.info(f"Updated existing agent: {agent_id} of type {agent_type} with endpoint {endpoint}")
        else:
            agent_status = AgentStatus(agent_id, agent_type)
            # Store endpoint in agent metadata
            agent_status.metadata["endpoint"] = endpoint
            self.agents[agent_id] = agent_status
            logger.info(f"Registered new agent: {agent_id} of type {agent_type} with endpoint {endpoint}")
        
        return {"status": "success", "agent_id": agent_id, "endpoint": endpoint}
    
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
            # Determine endpoint to use
            endpoint = agent.metadata.get("endpoint", self.agent_endpoints.get("default"))
            
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
    
    def create_workflow(self, workflow_type: str, parameters: Dict[str, Any]) -> Workflow:
        """
        Create a new workflow of the specified type
        
        Args:
            workflow_type: Type of workflow to create
            parameters: Parameters for the workflow
            
        Returns:
            The created Workflow object
            
        Raises:
            ValueError: If the workflow type is not found
        """
        if workflow_type not in self.workflow_modules:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
        
        try:
            # Create workflow using the module's get_workflow function
            workflow = self.workflow_modules[workflow_type].get_workflow(parameters)
            
            # Store the workflow
            self.workflows[workflow.id] = workflow
            logger.info(f"Created workflow: {workflow.name} (ID: {workflow.id}) with {len(workflow.steps)} steps")
            
            return workflow
            
        except Exception as e:
            logger.error(f"Error creating workflow '{workflow_type}': {str(e)}")
            raise ValueError(f"Workflow creation failed: {str(e)}")
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID"""
        return self.workflows.get(workflow_id)
    
    def execute_workflow(self, workflow_id: str) -> None:
        """
        Start executing a workflow in a separate thread
        
        Args:
            workflow_id: ID of the workflow to execute
            
        Raises:
            ValueError: If the workflow is not found
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
            
        # Update workflow status
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now()
        
        # In a real implementation, we would execute the workflow steps in a thread
        # For demo purposes, we'll just mark the first step as in progress
        if workflow.steps:
            workflow.steps[0].status = StepStatus.RUNNING
            
        logger.info(f"Started executing workflow: {workflow.name} (ID: {workflow.id})")
        
    def _setup_market_analysis_workflow(self, workflow: Workflow):
        """Set up steps for the market analysis and trade workflow"""
        workflow.add_step(WorkflowStep(
            id=f"{workflow.id}-step-1",
            name="collect_market_data",
            agent_id="market_data_agent",
            parameters={}
        ))
        workflow.add_step(WorkflowStep(
            id=f"{workflow.id}-step-2",
            name="analyze_market_trends",
            agent_id="market_analysis_agent",
            parameters={}
        ))
        workflow.add_step(WorkflowStep(
            id=f"{workflow.id}-step-3",
            name="identify_trading_opportunities",
            agent_id="trade_strategy_agent",
            parameters={}
        ))
        workflow.add_step(WorkflowStep(
            id=f"{workflow.id}-step-4",
            name="execute_trades",
            agent_id="trade_execution_agent",
            parameters={}
        ))
        workflow.add_step(WorkflowStep(
            id=f"{workflow.id}-step-5",
            name="update_portfolio",
            agent_id="portfolio_agent",
            parameters={}
        ))

    def _setup_portfolio_rebalance_workflow(self, workflow: Workflow):
        """Set up steps for the portfolio rebalance workflow"""
        workflow.add_step(WorkflowStep(
            id=f"{workflow.id}-step-1",
            name="analyze_current_portfolio",
            agent_id="portfolio_agent",
            parameters={}
        ))
        workflow.add_step(WorkflowStep(
            id=f"{workflow.id}-step-2",
            name="determine_optimal_allocation",
            agent_id="portfolio_optimization_agent",
            parameters={}
        ))
        workflow.add_step(WorkflowStep(
            id=f"{workflow.id}-step-3",
            name="plan_rebalance_trades",
            agent_id="trade_strategy_agent",
            parameters={}
        ))
        workflow.add_step(WorkflowStep(
            id=f"{workflow.id}-step-4",
            name="execute_rebalance_trades",
            agent_id="trade_execution_agent",
            parameters={}
        ))
        workflow.add_step(WorkflowStep(
            id=f"{workflow.id}-step-5",
            name="verify_portfolio_changes",
            agent_id="portfolio_agent",
            parameters={}
        ))

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a specific workflow"""
        if workflow_id not in self.workflows:
            return {
                "status": "error",
                "error": {
                    "code": "workflow_not_found",
                    "message": f"Workflow with ID {workflow_id} not found"
                }
            }
        
        # Update workflow status based on its steps
        workflow = self.workflows[workflow_id]
        workflow.status = WorkflowStatus.RUNNING if any(step.status == StepStatus.RUNNING for step in workflow.steps) else WorkflowStatus.PAUSED
        workflow.started_at = datetime.now() if workflow.status == WorkflowStatus.RUNNING else workflow.started_at
        workflow.completed_at = datetime.now() if workflow.status == WorkflowStatus.COMPLETED else workflow.completed_at
        
        return {
            "status": "success",
            "result": workflow.to_dict()
        }

    def call_function(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a function via the MCP protocol
        
        Args:
            function_name: The name of the function to call
            arguments: Dictionary of arguments to pass to the function
            
        Returns:
            A dictionary with the function result or error
        """
        if function_name not in self.function_to_agent:
            return {
                "status": "error",
                "error": {
                    "code": "function_not_found",
                    "message": f"Function {function_name} not found"
                }
            }
        
        try:
            # Call the function with the provided arguments
            agent_id = self.function_to_agent[function_name]
            agent = self.agents[agent_id]
            result = self.execute_function(function_name, arguments)
            
            # If the result is already formatted as a response, return it directly
            if isinstance(result, dict) and "status" in result:
                return result
                
            # Otherwise, wrap the result
            return {
                "status": "success",
                "result": result
            }
        except Exception as e:
            logger.error(f"Error executing function {function_name}: {str(e)}")
            return {
                "status": "error",
                "error": {
                    "code": "execution_error",
                    "message": str(e)
                }
            }

    # For simulating workflow progress in a real system
    def simulate_workflow_progress(self, workflow_id: str, step_index: int = None):
        """
        Simulate the progress of a workflow for testing/demonstration purposes
        
        Args:
            workflow_id: ID of the workflow to update
            step_index: Optional index of the step to complete; if None, advances the next pending step
        """
        if workflow_id not in self.workflows:
            return
            
        workflow = self.workflows[workflow_id]
        
        # If specific step provided, complete that step
        if step_index is not None and 0 <= step_index < len(workflow.steps):
            workflow.steps[step_index].status = StepStatus.COMPLETED
            
            # Start the next step if applicable
            if step_index + 1 < len(workflow.steps):
                workflow.steps[step_index + 1].status = StepStatus.RUNNING
        
        # Otherwise find the first in-progress step and complete it
        else:
            for i, step in enumerate(workflow.steps):
                if step.status == StepStatus.RUNNING:
                    step.status = StepStatus.COMPLETED
                    
                    # Start the next step if applicable
                    if i + 1 < len(workflow.steps):
                        workflow.steps[i + 1].status = StepStatus.RUNNING
                    break
        
        # Update workflow status
        workflow.status = WorkflowStatus.RUNNING if any(step.status == StepStatus.RUNNING for step in workflow.steps) else WorkflowStatus.PAUSED
        workflow.started_at = datetime.now() if workflow.status == WorkflowStatus.RUNNING else workflow.started_at
        workflow.completed_at = datetime.now() if workflow.status == WorkflowStatus.COMPLETED else workflow.completed_at


# Example usage
if __name__ == "__main__":
    # Initialize the orchestration agent
    orchestrator = OrchestrationAgent()
    
    # Register some agents
    orchestrator.register_agent("market_data_agent", "Market Data Agent")
    orchestrator.register_agent("market_analysis_agent", "Market Analysis Agent")
    orchestrator.register_agent("trade_strategy_agent", "Trade Strategy Agent")
    orchestrator.register_agent("trade_execution_agent", "Trade Execution Agent")
    orchestrator.register_agent("portfolio_agent", "Portfolio Agent")
    orchestrator.register_agent("portfolio_optimization_agent", "Portfolio Optimization Agent")
    
    # Load workflow modules
    orchestrator.load_workflow_modules()
    
    # Create and execute a workflow
    workflow = orchestrator.create_workflow("market_analysis_workflow", {
        "target_assets": ["BTC", "ETH", "SOL", "AVAX", "ADA"],
        "time_horizon": "medium",
        "trading_strategy": "balanced"
    })
    
    # Execute the workflow
    orchestrator.execute_workflow(workflow.id)
    
    # Simulate workflow progress for testing
    orchestrator.simulate_workflow_progress(workflow.id)
    orchestrator.simulate_workflow_progress(workflow.id)
    
    # Check workflow status
    workflow = orchestrator.get_workflow(workflow.id)
    print(f"Workflow status: {workflow.status.value}")
    print(f"Completed steps: {sum(1 for step in workflow.steps if step.status == StepStatus.COMPLETED)}/{len(workflow.steps)}")
    
    # Get agent status
    agent_status = orchestrator.get_agent("market_data_agent").to_dict()
    print(f"Agent status: {json.dumps(agent_status, indent=2)}")
    
    # Get all agents status
    all_agents_status = [agent.to_dict() for agent in orchestrator.get_all_agents()]
    print(f"All agents status: {json.dumps(all_agents_status, indent=2)}") 