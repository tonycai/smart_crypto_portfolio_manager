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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary representation"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "functions": self.functions,
            "status": self.status,
            "last_active": self.last_active.isoformat(),
            "metadata": self.metadata
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
    """
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.workflows: Dict[str, Workflow] = {}
        self.function_to_agent: Dict[str, str] = {}
        self.workflow_lock = threading.Lock()
        self.execution_threads: Dict[str, threading.Thread] = {}
        
        # Initialize workflow modules registry
        self.workflow_modules: Dict[str, Any] = {}
        self.load_workflow_modules()
        
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
    
    def register_agent(self, agent_data: Dict[str, Any]) -> Agent:
        """
        Register a new agent with the orchestration system
        
        Args:
            agent_data: Dictionary containing agent information
            
        Returns:
            The registered Agent object
        """
        # Create agent object
        agent = Agent(
            id=agent_data.get("id", str(uuid.uuid4())),
            name=agent_data.get("name", "Unknown Agent"),
            description=agent_data.get("description", ""),
            functions=agent_data.get("functions", []),
            metadata=agent_data.get("metadata", {})
        )
        
        # Store agent
        self.agents[agent.id] = agent
        
        # Update function-to-agent mapping
        for function_name in agent.functions:
            self.function_to_agent[function_name] = agent.id
            
        logger.info(f"Registered agent: {agent.name} (ID: {agent.id}) with {len(agent.functions)} functions")
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
            # In a real implementation, this would communicate with the agent
            # For demo purposes, we'll simulate the execution
            logger.info(f"Executing function '{function_name}' on agent '{agent.id}'")
            
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
        
class WorkflowStep:
    """Represents a single step in a workflow"""
    def __init__(self, step_id: str, step_name: str, agent_id: str):
        self.step_id = step_id
        self.step_name = step_name
        self.agent_id = agent_id
        self.status = "pending"  # pending, in_progress, completed, failed
        self.start_time = None
        self.end_time = None
        self.result = None
        self.error = None

    def start(self):
        """Mark the step as started"""
        self.status = "in_progress"
        self.start_time = datetime.now().isoformat()

    def complete(self, result: Any = None):
        """Mark the step as completed"""
        self.status = "completed"
        self.end_time = datetime.now().isoformat()
        self.result = result

    def fail(self, error: str):
        """Mark the step as failed"""
        self.status = "failed"
        self.end_time = datetime.now().isoformat()
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "step_id": self.step_id,
            "step_name": self.step_name,
            "status": self.status,
            "agent_id": self.agent_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "result": self.result,
            "error": self.error
        }


class Workflow:
    """Represents a workflow being executed by the Orchestration Agent"""
    def __init__(self, workflow_id: str, workflow_name: str, parameters: Dict[str, Any] = None):
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name
        self.parameters = parameters or {}
        self.steps: List[WorkflowStep] = []
        self.status = "pending"  # pending, in_progress, completed, failed
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.estimated_completion = None

    def add_step(self, step_name: str, agent_id: str) -> WorkflowStep:
        """Add a step to the workflow"""
        step_id = f"{self.workflow_id}-step-{len(self.steps) + 1}"
        step = WorkflowStep(step_id, step_name, agent_id)
        self.steps.append(step)
        return step

    def start(self):
        """Mark the workflow as started"""
        self.status = "in_progress"
        self.updated_at = datetime.now().isoformat()
        # Estimate completion time based on number of steps
        self.estimated_completion = (datetime.now() + timedelta(minutes=5 * len(self.steps))).isoformat()

    def update_status(self):
        """Update the workflow status based on its steps"""
        self.updated_at = datetime.now().isoformat()
        
        # Check if any steps failed
        if any(step.status == "failed" for step in self.steps):
            self.status = "failed"
            return
            
        # Check if all steps completed
        if all(step.status == "completed" for step in self.steps) and self.steps:
            self.status = "completed"
            return
            
        # Check if any steps are in progress
        if any(step.status == "in_progress" for step in self.steps):
            self.status = "in_progress"
            return
            
        # Otherwise, it's still pending
        self.status = "pending"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "status": self.status,
            "steps": [step.to_dict() for step in self.steps],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "estimated_completion": self.estimated_completion
        }


class OrchestrationAgent:
    """
    Main Orchestration Agent class that manages workflows, agent statuses, 
    and implements the Model Calling Protocol (MCP)
    """
    def __init__(self):
        self.agents: Dict[str, AgentStatus] = {}
        self.workflows: Dict[str, Workflow] = {}
        self.function_registry: Dict[str, Callable] = {}
        
        # Register built-in functions
        self._register_built_in_functions()
        logger.info("Orchestration Agent initialized")

    def _register_built_in_functions(self):
        """Register the built-in functions for the MCP protocol"""
        self.register_function("get_agent_status", self.get_agent_status)
        self.register_function("get_all_agents_status", self.get_all_agents_status)
        self.register_function("register_agent", self.register_agent)
        self.register_function("execute_workflow", self.execute_workflow)
        self.register_function("get_workflow_status", self.get_workflow_status)
        logger.info("Built-in functions registered")

    def register_function(self, function_name: str, function_impl: Callable):
        """Register a function that can be called via the MCP protocol"""
        self.function_registry[function_name] = function_impl
        logger.info(f"Registered function: {function_name}")

    def register_agent(self, agent_id: str, agent_type: str) -> Dict[str, Any]:
        """Register a new agent in the system or update an existing one"""
        if agent_id in self.agents:
            self.agents[agent_id].update_heartbeat()
            logger.info(f"Updated existing agent: {agent_id} of type {agent_type}")
        else:
            self.agents[agent_id] = AgentStatus(agent_id, agent_type)
            logger.info(f"Registered new agent: {agent_id} of type {agent_type}")
        
        return {"status": "success", "agent_id": agent_id}

    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get the status of a specific agent"""
        if agent_id not in self.agents:
            return {
                "status": "error", 
                "error": {
                    "code": "agent_not_found",
                    "message": f"Agent with ID {agent_id} not found"
                }
            }
        
        return {
            "status": "success",
            "result": self.agents[agent_id].to_dict()
        }

    def get_all_agents_status(self) -> Dict[str, Any]:
        """Get the status of all agents"""
        agents_list = [agent.to_dict() for agent in self.agents.values()]
        
        # Determine system health
        system_health = "healthy"
        error_count = sum(1 for agent in self.agents.values() if agent.status == "error")
        inactive_count = sum(1 for agent in self.agents.values() if agent.status == "inactive")
        
        if error_count > 0:
            system_health = "critical" if error_count > len(self.agents) // 3 else "degraded"
        elif inactive_count > len(self.agents) // 2:
            system_health = "degraded"
        
        return {
            "status": "success",
            "result": {
                "agents": agents_list,
                "system_health": system_health
            }
        }

    def execute_workflow(self, workflow_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create and execute a new workflow"""
        workflow_id = f"workflow-{uuid.uuid4()}"
        workflow = Workflow(workflow_id, workflow_name, parameters)
        
        # Add specific workflow steps based on the workflow name
        if workflow_name == "market_analysis_and_trade":
            self._setup_market_analysis_workflow(workflow)
        elif workflow_name == "portfolio_rebalance":
            self._setup_portfolio_rebalance_workflow(workflow)
        else:
            return {
                "status": "error",
                "error": {
                    "code": "unknown_workflow",
                    "message": f"Unknown workflow: {workflow_name}"
                }
            }
        
        # Start the workflow
        workflow.start()
        self.workflows[workflow_id] = workflow
        
        # In a real implementation, we would dispatch the workflow steps to their respective agents
        # For now, we'll just simulate the first step starting
        if workflow.steps:
            workflow.steps[0].start()
        
        logger.info(f"Executed workflow: {workflow_name} with ID {workflow_id}")
        return {
            "status": "success",
            "result": {
                "workflow_id": workflow_id,
                "status": workflow.status
            }
        }

    def _setup_market_analysis_workflow(self, workflow: Workflow):
        """Set up steps for the market analysis and trade workflow"""
        workflow.add_step("collect_market_data", "market_data_agent")
        workflow.add_step("analyze_market_trends", "market_analysis_agent")
        workflow.add_step("identify_trading_opportunities", "trade_strategy_agent")
        workflow.add_step("execute_trades", "trade_execution_agent")
        workflow.add_step("update_portfolio", "portfolio_agent")

    def _setup_portfolio_rebalance_workflow(self, workflow: Workflow):
        """Set up steps for the portfolio rebalance workflow"""
        workflow.add_step("analyze_current_portfolio", "portfolio_agent")
        workflow.add_step("determine_optimal_allocation", "portfolio_optimization_agent")
        workflow.add_step("plan_rebalance_trades", "trade_strategy_agent")
        workflow.add_step("execute_rebalance_trades", "trade_execution_agent")
        workflow.add_step("verify_portfolio_changes", "portfolio_agent")

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
        self.workflows[workflow_id].update_status()
        
        return {
            "status": "success",
            "result": self.workflows[workflow_id].to_dict()
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
        if function_name not in self.function_registry:
            return {
                "status": "error",
                "error": {
                    "code": "function_not_found",
                    "message": f"Function {function_name} not found"
                }
            }
        
        try:
            # Call the function with the provided arguments
            function = self.function_registry[function_name]
            result = function(**arguments)
            
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
            workflow.steps[step_index].complete({"sample": "result"})
            
            # Start the next step if applicable
            if step_index + 1 < len(workflow.steps):
                workflow.steps[step_index + 1].start()
        
        # Otherwise find the first in-progress step and complete it
        else:
            for i, step in enumerate(workflow.steps):
                if step.status == "in_progress":
                    step.complete({"sample": "result"})
                    
                    # Start the next step if applicable
                    if i + 1 < len(workflow.steps):
                        workflow.steps[i + 1].start()
                    break
        
        # Update workflow status
        workflow.update_status()


# Example usage
if __name__ == "__main__":
    # Initialize the orchestration agent
    orchestrator = OrchestrationAgent()
    
    # Register some agents
    orchestrator.register_agent("market_data_agent", "MarketData")
    orchestrator.register_agent("market_analysis_agent", "MarketAnalysis")
    orchestrator.register_agent("trade_strategy_agent", "TradeStrategy")
    orchestrator.register_agent("trade_execution_agent", "TradeExecution")
    orchestrator.register_agent("portfolio_agent", "Portfolio")
    
    # Execute a workflow
    response = orchestrator.execute_workflow("market_analysis_and_trade")
    print(f"Workflow executed: {json.dumps(response, indent=2)}")
    
    # Get the workflow ID
    workflow_id = response["result"]["workflow_id"]
    
    # Simulate workflow progress
    orchestrator.simulate_workflow_progress(workflow_id)
    orchestrator.simulate_workflow_progress(workflow_id)
    
    # Get workflow status
    status_response = orchestrator.get_workflow_status(workflow_id)
    print(f"Workflow status: {json.dumps(status_response, indent=2)}")
    
    # Get agent status
    agent_status = orchestrator.get_agent_status("market_data_agent")
    print(f"Agent status: {json.dumps(agent_status, indent=2)}")
    
    # Get all agents status
    all_agents_status = orchestrator.get_all_agents_status()
    print(f"All agents status: {json.dumps(all_agents_status, indent=2)}") 