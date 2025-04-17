#!/usr/bin/env python3
"""
Main entry point for the Smart Crypto Portfolio Manager system.
This script initializes and starts all agents.
"""

import os
import sys
import argparse
import asyncio
import logging
from typing import Dict, List, Any

# Import agent modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from agents.market_analysis.agent import MarketAnalysisAgent
from agents.trade_execution.agent import TradeExecutionAgent
from agents.risk_management.agent import RiskManagementAgent
from agents.reporting_analytics.agent import ReportingAnalyticsAgent


async def start_market_analysis_agent(host: str, port: int, config_path: str = None):
    """Start the Market Analysis Agent."""
    agent = MarketAnalysisAgent(config_path=config_path)
    await agent.start(host=host, port=port)


async def start_trade_execution_agent(host: str, port: int, config_path: str = None):
    """Start the Trade Execution Agent."""
    agent = TradeExecutionAgent(config_path=config_path)
    await agent.start(host=host, port=port)


async def start_risk_management_agent(host: str, port: int, config_path: str = None):
    """Start the Risk Management Agent."""
    agent = RiskManagementAgent(config_path=config_path)
    await agent.start(host=host, port=port)


async def start_reporting_analytics_agent(host: str, port: int, config_path: str = None):
    """Start the Reporting and Analytics Agent."""
    agent = ReportingAnalyticsAgent(config_path=config_path)
    await agent.start(host=host, port=port)


async def main():
    """Main entry point for the Smart Crypto Portfolio Manager system."""
    parser = argparse.ArgumentParser(description='Start the Smart Crypto Portfolio Manager system')
    parser.add_argument('--market-analysis-host', default='0.0.0.0', help='Host for Market Analysis Agent')
    parser.add_argument('--market-analysis-port', type=int, default=8001, help='Port for Market Analysis Agent')
    parser.add_argument('--market-analysis-config', help='Config file for Market Analysis Agent')
    
    parser.add_argument('--trade-execution-host', default='0.0.0.0', help='Host for Trade Execution Agent')
    parser.add_argument('--trade-execution-port', type=int, default=8002, help='Port for Trade Execution Agent')
    parser.add_argument('--trade-execution-config', help='Config file for Trade Execution Agent')
    
    parser.add_argument('--risk-management-host', default='0.0.0.0', help='Host for Risk Management Agent')
    parser.add_argument('--risk-management-port', type=int, default=8003, help='Port for Risk Management Agent')
    parser.add_argument('--risk-management-config', help='Config file for Risk Management Agent')
    
    parser.add_argument('--reporting-analytics-host', default='0.0.0.0', help='Host for Reporting Analytics Agent')
    parser.add_argument('--reporting-analytics-port', type=int, default=8004, help='Port for Reporting Analytics Agent')
    parser.add_argument('--reporting-analytics-config', help='Config file for Reporting Analytics Agent')
    
    parser.add_argument('--log-level', default='INFO', 
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Logging level')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('SmartCryptoPortfolioManager')
    
    logger.info("Starting Smart Crypto Portfolio Manager system")
    
    # Start all agents
    try:
        # In a real implementation, these would run in separate processes or containers
        # For this prototype, we'll start all agents in separate tasks
        await asyncio.gather(
            start_market_analysis_agent(
                host=args.market_analysis_host,
                port=args.market_analysis_port,
                config_path=args.market_analysis_config
            ),
            start_trade_execution_agent(
                host=args.trade_execution_host,
                port=args.trade_execution_port,
                config_path=args.trade_execution_config
            ),
            start_risk_management_agent(
                host=args.risk_management_host,
                port=args.risk_management_port,
                config_path=args.risk_management_config
            ),
            start_reporting_analytics_agent(
                host=args.reporting_analytics_host,
                port=args.reporting_analytics_port,
                config_path=args.reporting_analytics_config
            )
        )
    except Exception as e:
        logger.error(f"Error starting agents: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
