"""
Trade Execution Agent for Smart Crypto Portfolio Manager

This agent executes buy and sell orders on various crypto exchanges based on signals
received from other agents.
"""

import os
import json
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

import uvicorn
from fastapi import FastAPI

# Import the A2A server implementation
import sys
# Use relative import path instead of hardcoded path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from a2a.server import create_a2a_server
from a2a.client import A2AClient


class TradeExecutionAgent:
    """
    Agent for executing cryptocurrency trades on various exchanges.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the Trade Execution Agent.
        
        Args:
            config_path: Path to the configuration file (optional)
        """
        self.name = "Trade Execution Agent"
        self.version = "1.0.0"
        
        # Load configuration if provided
        self.config = {}
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.name)
        
        # Initialize the A2A client for communicating with other agents
        self.a2a_client = A2AClient(self.name, self.version)
        
        # Create the A2A server
        agent_card_path = os.path.join(os.path.dirname(__file__), 'agent.json')
        self.a2a_server = create_a2a_server(agent_card_path)
        
        # Register capability handlers
        self.a2a_server.register_capability_handler('execute_trade', self.execute_trade)
        self.a2a_server.register_capability_handler('get_order_status', self.get_order_status)
        
        # Initialize exchange API connectors
        self.exchange_connectors = {}
        self._initialize_exchange_connectors()
        
        # In-memory order storage for simulation
        self.orders = {}
    
    def _initialize_exchange_connectors(self):
        """
        Initialize connections to configured exchanges.
        In a real implementation, this would set up API clients for each exchange.
        """
        exchanges = self.config.get('exchanges', [])
        for exchange in exchanges:
            if exchange.get('is_enabled', False):
                exchange_name = exchange['name']
                self.logger.info(f"Initializing connector for {exchange_name}")
                # In a real implementation, this would create appropriate exchange API clients
                # e.g., ccxt or exchange-specific libraries
                self.exchange_connectors[exchange_name] = {
                    'api_key': exchange.get('api_key'),
                    'api_secret': exchange.get('api_secret'),
                    'enabled': True
                }
    
    async def execute_trade(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trade on a specified crypto exchange.
        
        Args:
            parameters: Parameters for the trade execution
            
        Returns:
            Trade execution results
        """
        self.logger.info(f"Executing trade: {parameters}")
        
        # Extract parameters
        exchange = parameters.get('exchange')
        crypto_pair = parameters.get('crypto_pair')
        action = parameters.get('action')
        order_type = parameters.get('order_type')
        quantity = parameters.get('quantity')
        price = parameters.get('price')
        
        # Validate required parameters
        if not exchange or not crypto_pair or not action or not order_type or quantity is None:
            raise ValueError("Missing required parameters for trade execution")
        
        # Check if the exchange is configured
        if exchange not in self.exchange_connectors:
            raise ValueError(f"Exchange {exchange} not configured or not enabled")
        
        # In a real implementation, this would call the exchange API
        # For this prototype, we'll simulate a trade execution
        order_id = str(uuid.uuid4())
        execution_time = datetime.utcnow().isoformat()
        
        # Simulate market price if not provided for a market order
        executed_price = price if price is not None else self._simulate_market_price(crypto_pair)
        
        # Simulate order execution
        executed_quantity = quantity
        
        # Store the order in our in-memory database
        self.orders[order_id] = {
            'order_id': order_id,
            'exchange': exchange,
            'crypto_pair': crypto_pair,
            'action': action,
            'order_type': order_type,
            'quantity': quantity,
            'price': price,
            'executed_price': executed_price,
            'executed_quantity': executed_quantity,
            'status': 'filled',  # For simulation, we'll assume all orders are filled immediately
            'timestamp': execution_time
        }
        
        # Notify the Risk Management Agent
        await self._notify_risk_management(order_id)
        
        # Notify the Reporting Agent
        await self._notify_reporting(order_id)
        
        return {
            'order_id': order_id,
            'status': 'filled',
            'executed_price': executed_price,
            'executed_quantity': executed_quantity,
            'timestamp': execution_time
        }
    
    async def get_order_status(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the current status of an order.
        
        Args:
            parameters: Parameters for the order status request
            
        Returns:
            Order status details
        """
        self.logger.info(f"Getting order status: {parameters}")
        
        # Extract parameters
        exchange = parameters.get('exchange')
        order_id = parameters.get('order_id')
        
        # Validate required parameters
        if not exchange or not order_id:
            raise ValueError("Missing required parameters for order status")
        
        # Check if the exchange is configured
        if exchange not in self.exchange_connectors:
            raise ValueError(f"Exchange {exchange} not configured or not enabled")
        
        # In a real implementation, this would call the exchange API
        # For this prototype, we'll return the order from our in-memory database
        if order_id not in self.orders:
            raise ValueError(f"Order {order_id} not found")
        
        order = self.orders[order_id]
        
        return {
            'status': order['status'],
            'executed_price': order['executed_price'],
            'executed_quantity': order['executed_quantity'],
            'remaining_quantity': 0  # For simulation, we assume all orders are fully executed
        }
    
    def _simulate_market_price(self, crypto_pair: str) -> float:
        """
        Simulate a market price for a crypto pair.
        
        Args:
            crypto_pair: The cryptocurrency trading pair
            
        Returns:
            Simulated market price
        """
        # This is a very simple price simulation
        # In a real implementation, we would fetch the current price from an exchange
        base_prices = {
            'BTC/USD': 50000,
            'ETH/USD': 3000,
            'SOL/USD': 100,
            'ADA/USD': 1,
            'DOT/USD': 20
        }
        
        # Use the base price if available, otherwise generate a random price
        if crypto_pair in base_prices:
            base_price = base_prices[crypto_pair]
        else:
            base_price = 100
        
        # Add some randomness to simulate market fluctuations
        import random
        price_variation = random.uniform(-0.02, 0.02)  # +/- 2%
        return base_price * (1 + price_variation)
    
    async def _notify_risk_management(self, order_id: str):
        """
        Notify the Risk Management Agent about a trade execution.
        
        Args:
            order_id: ID of the executed order
        """
        if 'a2a' in self.config and 'risk_management_agent' in self.config['a2a']:
            risk_agent_url = self.config['a2a']['risk_management_agent']
            try:
                # Discover the Risk Management Agent
                risk_agent = self.a2a_client.discover_agent(risk_agent_url)
                
                # Get the order details
                order = self.orders[order_id]
                
                # Create a task to update portfolio risk
                self.a2a_client.create_task(
                    agent_name=risk_agent['name'],
                    capability='update_portfolio',
                    parameters={
                        'order_id': order_id,
                        'exchange': order['exchange'],
                        'crypto_pair': order['crypto_pair'],
                        'action': order['action'],
                        'quantity': order['quantity'],
                        'executed_price': order['executed_price']
                    }
                )
                
                self.logger.info(f"Risk Management Agent notified about order {order_id}")
            except Exception as e:
                self.logger.error(f"Failed to notify Risk Management Agent: {e}")
    
    async def _notify_reporting(self, order_id: str):
        """
        Notify the Reporting and Analytics Agent about a trade execution.
        
        Args:
            order_id: ID of the executed order
        """
        if 'a2a' in self.config and 'reporting_analytics_agent' in self.config['a2a']:
            reporting_agent_url = self.config['a2a']['reporting_analytics_agent']
            try:
                # Discover the Reporting and Analytics Agent
                reporting_agent = self.a2a_client.discover_agent(reporting_agent_url)
                
                # Get the order details
                order = self.orders[order_id]
                
                # Create a task to log the trade
                self.a2a_client.create_task(
                    agent_name=reporting_agent['name'],
                    capability='log_trade',
                    parameters={
                        'order_id': order_id,
                        'exchange': order['exchange'],
                        'crypto_pair': order['crypto_pair'],
                        'action': order['action'],
                        'order_type': order['order_type'],
                        'quantity': order['quantity'],
                        'executed_price': order['executed_price'],
                        'timestamp': order['timestamp']
                    }
                )
                
                self.logger.info(f"Reporting and Analytics Agent notified about order {order_id}")
            except Exception as e:
                self.logger.error(f"Failed to notify Reporting and Analytics Agent: {e}")
    
    async def start(self, host: str = "0.0.0.0", port: int = 8002):
        """
        Start the Trade Execution Agent.
        
        Args:
            host: Host to bind the server to
            port: Port to bind the server to
        """
        app = self.a2a_server.app
        
        # Add root endpoint for health checks
        @app.get("/")
        async def root():
            return {"status": "ok", "agent": self.name, "version": self.version}
        
        self.logger.info(f"Starting Trade Execution Agent on {host}:{port}")
        
        # Configure and start the server
        config = uvicorn.Config(app, host=host, port=port)
        server = uvicorn.Server(config)
        await server.serve()


async def main():
    """Main entry point for the Trade Execution Agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Start the Trade Execution Agent')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind the server to')
    parser.add_argument('--port', type=int, default=8002, help='Port to bind the server to')
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
    agent = TradeExecutionAgent(config_path=args.config)
    await agent.start(host=args.host, port=args.port)


if __name__ == "__main__":
    asyncio.run(main())