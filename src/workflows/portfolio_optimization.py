"""
Portfolio Optimization Workflow

This workflow orchestrates the process of optimizing a cryptocurrency portfolio
through multiple steps including data collection, analysis, and strategy generation.
"""

import logging
from typing import Dict, Any, List, Optional

from src.workflows.base_workflow import BaseWorkflow
from src.workflows import WorkflowStatus

logger = logging.getLogger(__name__)

class PortfolioOptimizationWorkflow(BaseWorkflow):
    """
    A workflow for optimizing cryptocurrency portfolios.
    
    This workflow orchestrates the following steps:
    1. Fetch market data for target assets
    2. Analyze market trends and correlations
    3. Generate investment strategy based on risk profile
    4. Prepare trade execution plan
    5. (Optional) Execute trades or provide recommendations
    """
    
    def __init__(
        self,
        workflow_id: str = None,
        parameters: Dict[str, Any] = None
    ):
        """
        Initialize a portfolio optimization workflow
        
        Args:
            workflow_id: Optional workflow ID
            parameters: Workflow parameters including:
                - risk_tolerance: Risk tolerance level (low, medium, high)
                - investment_horizon: Investment horizon in days
                - target_assets: List of cryptocurrency symbols to include
                - initial_allocation: Current portfolio allocation
                - constraints: Any constraints on the optimization
        """
        super().__init__(
            workflow_id=workflow_id,
            name="Portfolio Optimization",
            description="Optimize a cryptocurrency portfolio based on risk profile and market data",
            parameters=parameters or {}
        )
        
        self._validate_parameters()
        self.define_steps()
        
    def _validate_parameters(self) -> None:
        """Validate the workflow parameters"""
        required_params = ["risk_tolerance", "investment_horizon", "target_assets"]
        for param in required_params:
            if param not in self.parameters:
                raise ValueError(f"Missing required parameter: {param}")
        
        # Validate risk_tolerance
        valid_risk_levels = ["low", "medium", "high"]
        if self.parameters["risk_tolerance"] not in valid_risk_levels:
            raise ValueError(f"Invalid risk_tolerance. Must be one of: {valid_risk_levels}")
        
        # Validate investment_horizon
        try:
            horizon = int(self.parameters["investment_horizon"])
            if horizon <= 0:
                raise ValueError("Investment horizon must be a positive number")
        except (ValueError, TypeError):
            raise ValueError("Investment horizon must be a positive number")
        
        # Validate target_assets
        if not isinstance(self.parameters["target_assets"], list) or len(self.parameters["target_assets"]) == 0:
            raise ValueError("target_assets must be a non-empty list of asset symbols")
    
    def define_steps(self) -> None:
        """Define the workflow steps"""
        # Step 1: Fetch market data
        fetch_data_step_id = self.add_step(
            name="Fetch Market Data",
            agent_id="market_data_agent",
            function_name="fetch_market_data",
            function_args={
                "symbols": self.parameters["target_assets"],
                "lookback_days": 30  # Default to 30 days of historical data
            }
        )
        
        # Step 2: Analyze market trends
        analyze_trends_step_id = self.add_step(
            name="Analyze Market Trends",
            agent_id="analysis_agent",
            function_name="analyze_market_trends",
            function_args={
                "risk_tolerance": self.parameters["risk_tolerance"]
            },
            dependencies=[fetch_data_step_id]
        )
        
        # Step 3: Calculate asset correlations
        correlations_step_id = self.add_step(
            name="Calculate Asset Correlations",
            agent_id="analysis_agent",
            function_name="calculate_correlations",
            dependencies=[fetch_data_step_id]
        )
        
        # Step 4: Generate investment strategy
        strategy_step_id = self.add_step(
            name="Generate Investment Strategy",
            agent_id="strategy_agent",
            function_name="generate_strategy",
            function_args={
                "risk_tolerance": self.parameters["risk_tolerance"],
                "investment_horizon": self.parameters["investment_horizon"],
                "initial_allocation": self.parameters.get("initial_allocation", {})
            },
            dependencies=[analyze_trends_step_id, correlations_step_id]
        )
        
        # Step 5: Prepare trade execution plan
        trade_plan_step_id = self.add_step(
            name="Prepare Trade Execution Plan",
            agent_id="trade_planning_agent",
            function_name="prepare_trade_plan",
            function_args={
                "constraints": self.parameters.get("constraints", {})
            },
            dependencies=[strategy_step_id]
        )
        
        # Step 6: Execute trades (optional, based on parameters)
        if self.parameters.get("auto_execute", False):
            self.add_step(
                name="Execute Trades",
                agent_id="execution_agent",
                function_name="execute_trades",
                dependencies=[trade_plan_step_id]
            )

def get_workflow(parameters: Dict[str, Any]) -> PortfolioOptimizationWorkflow:
    """
    Create a portfolio optimization workflow
    
    Args:
        parameters: Workflow parameters including:
            - risk_tolerance: Risk tolerance level (low, medium, high)
            - investment_horizon: Investment horizon in days
            - target_assets: List of cryptocurrency symbols to include
            - initial_allocation: Current portfolio allocation (optional)
            - constraints: Any constraints on the optimization (optional)
            - auto_execute: Whether to auto-execute trades (optional, default False)
            
    Returns:
        A configured portfolio optimization workflow
    """
    try:
        workflow = PortfolioOptimizationWorkflow(parameters=parameters)
        logger.info(f"Created portfolio optimization workflow: {workflow.workflow_id}")
        return workflow
    except ValueError as e:
        logger.error(f"Failed to create portfolio optimization workflow: {str(e)}")
        raise

def simulate_step_execution(workflow: PortfolioOptimizationWorkflow, step_id: str, result: Any = None) -> None:
    """
    Simulate the execution of a workflow step (for testing/demo purposes)
    
    Args:
        workflow: The workflow instance
        step_id: ID of the step to simulate
        result: Optional result to set for the step
    """
    step = workflow.steps.get(step_id)
    if not step:
        raise ValueError(f"Step {step_id} not found in workflow")
    
    logger.info(f"Simulating execution of step: {step.name}")
    
    step.start()
    
    # Generate sample results based on step name if not provided
    if result is None:
        if step.name == "Fetch Market Data":
            result = {
                "data": {symbol: {"prices": [100 + i for i in range(30)]} for symbol in workflow.parameters["target_assets"]},
                "timestamp": "2023-09-01T00:00:00Z"
            }
        elif step.name == "Analyze Market Trends":
            result = {
                "trends": {symbol: {"direction": "up", "strength": 0.8} for symbol in workflow.parameters["target_assets"]},
                "summary": "Overall positive market sentiment detected"
            }
        elif step.name == "Calculate Asset Correlations":
            assets = workflow.parameters["target_assets"]
            result = {
                "correlation_matrix": {a: {b: 0.5 for b in assets} for a in assets},
                "clusters": [{"assets": assets, "correlation": 0.5}]
            }
        elif step.name == "Generate Investment Strategy":
            result = {
                "target_allocation": {symbol: 1.0/len(workflow.parameters["target_assets"]) for symbol in workflow.parameters["target_assets"]},
                "rebalance_frequency": "weekly"
            }
        elif step.name == "Prepare Trade Execution Plan":
            result = {
                "trades": [{"symbol": symbol, "action": "buy", "amount": 100.0} for symbol in workflow.parameters["target_assets"]],
                "estimated_cost": 1000.0
            }
        elif step.name == "Execute Trades":
            result = {
                "executed_trades": [{"symbol": symbol, "action": "buy", "amount": 100.0, "status": "completed"} for symbol in workflow.parameters["target_assets"]],
                "total_cost": 1050.0
            }
        else:
            result = {"status": "completed"}
    
    step.complete(result)
    logger.info(f"Completed step: {step.name}")

def create_workflow(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Legacy function to create a workflow in the old format (for compatibility)
    
    Args:
        parameters: Workflow parameters
    
    Returns:
        A dictionary representing the workflow in the old format
    """
    # Create the new format workflow
    workflow = get_workflow(parameters)
    
    # Convert to the old format
    old_format = {
        "workflow_id": workflow.workflow_id,
        "name": workflow.name,
        "description": workflow.description,
        "parameters": workflow.parameters,
        "steps": [],
        "status": "PENDING",
        "created_at": workflow.created_at.isoformat()
    }
    
    # Add steps in the old format
    execution_plan = workflow.get_execution_plan()
    step_level = 0
    
    for level in execution_plan:
        for step_id in level:
            step = workflow.steps[step_id]
            old_format["steps"].append({
                "step_id": step.step_id,
                "name": step.name,
                "agent_id": step.agent_id,
                "function": step.function_name,
                "arguments": step.function_args,
                "dependencies": step.dependencies,
                "level": step_level
            })
        step_level += 1
    
    return old_format 