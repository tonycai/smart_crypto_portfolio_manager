#!/usr/bin/env python3
import logging
import json
import time
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Demo")

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import the orchestration agent
from src.agents.orchestration_agent import OrchestrationAgent, Agent, AgentStatus

def main():
    """
    Demo script for the Smart Crypto Portfolio Manager
    Shows how to use the OrchestrationAgent with workflows
    """
    logger.info("Starting Smart Crypto Portfolio Manager Demo")
    
    # Create the orchestration agent
    orchestration_agent = OrchestrationAgent()
    
    # Register some mock agents
    register_mock_agents(orchestration_agent)
    
    # List available agents
    list_available_agents(orchestration_agent)
    
    # Create and execute a portfolio optimization workflow
    create_and_execute_workflow(orchestration_agent)
    
    logger.info("Demo completed successfully")

def register_mock_agents(orchestration_agent):
    """Register mock agents for the demo"""
    # Market Data Agent
    market_data_agent = {
        "id": "market-data-agent-001",
        "name": "Market Data Agent",
        "description": "Provides access to cryptocurrency market data",
        "functions": ["fetch_market_data", "fetch_historical_prices", "fetch_trading_volume"],
        "metadata": {
            "supported_exchanges": ["Binance", "Coinbase", "Kraken"]
        }
    }
    orchestration_agent.register_agent(market_data_agent)
    
    # Market Analysis Agent
    market_analysis_agent = {
        "id": "market-analysis-agent-001",
        "name": "Market Analysis Agent",
        "description": "Analyzes market trends and patterns",
        "functions": ["analyze_market_trends", "analyze_volatility", "analyze_correlations"],
        "metadata": {
            "analysis_methods": ["Technical", "Statistical", "Sentiment"]
        }
    }
    orchestration_agent.register_agent(market_analysis_agent)
    
    # Strategy Generator Agent
    strategy_agent = {
        "id": "strategy-agent-001",
        "name": "Strategy Generator Agent",
        "description": "Generates trading strategies based on market analysis",
        "functions": ["generate_trading_strategy", "generate_investment_recommendations"],
        "metadata": {
            "strategy_types": ["Momentum", "Mean Reversion", "Trend Following"]
        }
    }
    orchestration_agent.register_agent(strategy_agent)
    
    # Portfolio Optimization Agent
    portfolio_agent = {
        "id": "portfolio-agent-001",
        "name": "Portfolio Optimization Agent",
        "description": "Optimizes portfolio allocation based on strategy and risk parameters",
        "functions": ["optimize_portfolio_allocation", "calculate_expected_returns"],
        "metadata": {
            "optimization_methods": ["Modern Portfolio Theory", "Risk Parity", "Black-Litterman"]
        }
    }
    orchestration_agent.register_agent(portfolio_agent)
    
    # Trade Execution Agent
    trade_agent = {
        "id": "trade-agent-001",
        "name": "Trade Execution Agent",
        "description": "Prepares and executes trades across exchanges",
        "functions": ["prepare_trade_execution", "simulate_trades"],
        "metadata": {
            "supported_exchanges": ["Binance", "Coinbase", "Kraken"]
        }
    }
    orchestration_agent.register_agent(trade_agent)
    
    logger.info(f"Registered {len(orchestration_agent.agents)} mock agents")

def list_available_agents(orchestration_agent):
    """List all available agents"""
    agents = orchestration_agent.get_all_agents()
    logger.info(f"Available Agents ({len(agents)}):")
    
    for agent in agents:
        logger.info(f"  - {agent.name} (ID: {agent.id})")
        logger.info(f"    Functions: {', '.join(agent.functions)}")

def create_and_execute_workflow(orchestration_agent):
    """Create and execute a portfolio optimization workflow"""
    # Parameters for our workflow
    workflow_params = {
        "risk_tolerance": "medium",
        "investment_horizon": "medium",  # short, medium, long
        "target_assets": ["BTC", "ETH", "SOL", "AVAX", "ADA"],
        "initial_allocation": {
            "BTC": 0.35,
            "ETH": 0.25,
            "SOL": 0.15,
            "AVAX": 0.15,
            "ADA": 0.10
        },
        "preferences": {
            "max_allocation_per_asset": 0.5,
            "min_allocation_per_asset": 0.05,
            "max_allocation_crypto": 0.9,  # max percentage in crypto vs stable/fiat
            "rebalance_threshold": 0.1,    # rebalance when allocation drifts by this percentage
        }
    }
    
    try:
        # Create the workflow
        workflow = orchestration_agent.create_workflow("portfolio_optimization", workflow_params)
        
        # Print workflow details
        logger.info(f"Created workflow: {workflow.name} (ID: {workflow.id})")
        logger.info(f"Number of steps: {len(workflow.steps)}")
        logger.info("Workflow steps:")
        
        for i, step in enumerate(workflow.steps):
            depends_on = ", ".join(step.depends_on) if step.depends_on else "None"
            logger.info(f"  {i+1}. {step.name} (ID: {step.id}, Agent: {step.agent_id}, Depends on: {depends_on})")
        
        # Execute the workflow
        logger.info(f"Starting workflow execution...")
        orchestration_agent.execute_workflow(workflow.id)
        
        # For demo purposes, we'll manually advance the workflow steps
        # In a real system, this would happen asynchronously based on agent responses
        logger.info("Simulating workflow execution...")
        
        # Wait for the workflow to complete or fail
        max_wait_time = 30  # seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            # Get the latest workflow state
            workflow = orchestration_agent.get_workflow(workflow.id)
            
            # Print current status
            logger.info(f"Workflow status: {workflow.status}")
            
            completed_steps = sum(1 for step in workflow.steps if step.status == "COMPLETED")
            total_steps = len(workflow.steps)
            logger.info(f"Progress: {completed_steps}/{total_steps} steps completed")
            
            # Manually advance the workflow for demo purposes
            orchestration_agent.advance_workflow_step(workflow.id)
            
            # Check if workflow is completed or failed
            if workflow.status in ["COMPLETED", "FAILED"]:
                break
                
            # Wait before checking again
            time.sleep(2)
            
        # Print final workflow results
        workflow = orchestration_agent.get_workflow(workflow.id)
        logger.info(f"Workflow final status: {workflow.status}")
        
        if workflow.status == "COMPLETED":
            logger.info("Workflow completed successfully!")
            logger.info("Results:")
            
            # Print the final results from each step
            for step in workflow.steps:
                if step.result:
                    logger.info(f"  - {step.name}: {json.dumps(step.result, indent=2)}")
                    
            # Get the final trade execution plan
            final_step = workflow.steps[-1]
            if final_step.result and "trades" in final_step.result:
                logger.info("Recommended trades:")
                for trade in final_step.result["trades"]:
                    logger.info(f"  - {trade['action']} {trade['amount']} of {trade['asset']}")
        else:
            logger.error("Workflow failed to complete")
            # Print any error messages
            for step in workflow.steps:
                if step.status == "FAILED":
                    logger.error(f"  - Step '{step.name}' failed: {step.error_message}")
    
    except Exception as e:
        logger.error(f"Error during workflow execution: {str(e)}")

if __name__ == "__main__":
    main() 