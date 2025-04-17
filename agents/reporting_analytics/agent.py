"""
Reporting and Analytics Agent for Smart Crypto Portfolio Manager

This agent generates reports on trading performance, portfolio valuation, and risk metrics.
"""

import os
import json
import asyncio
import logging
import uuid
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import uvicorn
from fastapi import FastAPI

# Import the A2A server implementation
import sys
# Use relative import path instead of hardcoded path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from a2a.server import create_a2a_server
from a2a.client import A2AClient


class ReportingAnalyticsAgent:
    """
    Agent for generating reports and analytics for cryptocurrency trading.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the Reporting and Analytics Agent.
        
        Args:
            config_path: Path to the configuration file (optional)
        """
        self.name = "Reporting and Analytics Agent"
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
        self.a2a_server.register_capability_handler('generate_performance_report', self.generate_performance_report)
        self.a2a_server.register_capability_handler('generate_portfolio_valuation', self.generate_portfolio_valuation)
        self.a2a_server.register_capability_handler('log_trade', self.log_trade)
        
        # Initialize data stores
        self.trades = []
        self.reports = {}
        self.portfolio = {}
        
        # Load initial data
        self._load_data()
    
    def _load_data(self):
        """
        Load initial data.
        In a real implementation, this would load from a database or storage service.
        """
        # For this prototype, we'll initialize with empty data
        # or load from a predefined configuration
        self.trades = self.config.get('initial_trades', [])
    
    async def generate_performance_report(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive performance report for the portfolio.
        
        Args:
            parameters: Parameters for the report generation
            
        Returns:
            Performance report data
        """
        self.logger.info(f"Generating performance report: {parameters}")
        
        # Extract parameters
        time_period = parameters.get('time_period', 'month')
        start_date = parameters.get('start_date')
        end_date = parameters.get('end_date')
        include_metrics = parameters.get('include_metrics', ['total_return', 'daily_returns', 'trade_statistics'])
        report_format = parameters.get('format', 'json')
        
        # Determine the date range
        end_datetime = datetime.utcnow()
        if end_date:
            end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        start_datetime = None
        if start_date:
            start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            # Calculate start date based on time period
            if time_period == 'day':
                start_datetime = end_datetime - timedelta(days=1)
            elif time_period == 'week':
                start_datetime = end_datetime - timedelta(days=7)
            elif time_period == 'month':
                start_datetime = end_datetime - timedelta(days=30)
            elif time_period == 'quarter':
                start_datetime = end_datetime - timedelta(days=90)
            elif time_period == 'year':
                start_datetime = end_datetime - timedelta(days=365)
            else:
                start_datetime = end_datetime - timedelta(days=30)  # Default to month
        
        # Filter trades for the specified date range
        filtered_trades = [
            trade for trade in self.trades
            if start_datetime <= datetime.fromisoformat(trade['timestamp'].replace('Z', '+00:00')) <= end_datetime
        ]
        
        # Calculate performance metrics
        total_return, total_return_pct = self._calculate_total_return(filtered_trades)
        
        # Calculate annualized return
        days = (end_datetime - start_datetime).days
        annualized_return_pct = ((1 + total_return_pct) ** (365 / max(days, 1))) - 1 if days > 0 else 0
        
        # Calculate other metrics
        daily_returns = self._calculate_daily_returns(filtered_trades, start_datetime, end_datetime)
        max_drawdown = self._calculate_max_drawdown(daily_returns)
        sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
        trade_statistics = self._calculate_trade_statistics(filtered_trades)
        
        # Generate a report ID
        report_id = str(uuid.uuid4())
        
        # Create a summary of the report
        summary = {
            'total_return_pct': total_return_pct * 100,  # Convert to percentage
            'annualized_return_pct': annualized_return_pct * 100,  # Convert to percentage
            'max_drawdown_pct': max_drawdown * 100,  # Convert to percentage
            'sharpe_ratio': sharpe_ratio
        }
        
        # Create the full report data
        report_data = {
            'summary': summary,
            'time_period': time_period,
            'start_date': start_datetime.isoformat(),
            'end_date': end_datetime.isoformat(),
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'annualized_return_pct': annualized_return_pct,
            'daily_returns': daily_returns,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'trade_statistics': trade_statistics
        }
        
        # Store the report
        self.reports[report_id] = {
            'id': report_id,
            'type': 'performance',
            'data': report_data,
            'created_at': datetime.utcnow().isoformat()
        }
        
        # In a real implementation, you would generate different format outputs
        # like PDF, HTML, etc. For this prototype, we'll just return the JSON data
        
        return {
            'report_id': report_id,
            'summary': summary,
            'report_url': f"/reports/{report_id}",
            'report_data': report_data if report_format == 'json' else None
        }
    
    async def generate_portfolio_valuation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a current portfolio valuation report.
        
        Args:
            parameters: Parameters for the valuation report
            
        Returns:
            Portfolio valuation data
        """
        self.logger.info(f"Generating portfolio valuation: {parameters}")
        
        # Extract parameters
        include_details = parameters.get('include_details', True)
        valuation_currency = parameters.get('valuation_currency', 'USD')
        report_format = parameters.get('format', 'json')
        
        # Get the current portfolio data
        # In a real implementation, this would come from a database or from 
        # the Risk Management Agent via an A2A request
        
        # For this prototype, we'll simulate portfolio data
        portfolio = self._get_current_portfolio()
        total_value = 0
        assets = []
        
        for crypto, details in portfolio.items():
            # Get the current price
            current_price = self._get_current_price(crypto)
            
            # Calculate the value
            value = details['quantity'] * current_price
            total_value += value
            
            # 24-hour change (simulated)
            change_24h = self._get_24h_price_change(crypto)
            
            assets.append({
                'crypto': crypto,
                'quantity': details['quantity'],
                'value': value,
                'price': current_price,
                '24h_change_pct': change_24h * 100  # Convert to percentage
            })
        
        # Calculate allocation percentages
        for asset in assets:
            asset['allocation_pct'] = (asset['value'] / total_value * 100) if total_value > 0 else 0
        
        # Generate a report ID
        report_id = str(uuid.uuid4())
        
        # Create the valuation data
        valuation_data = {
            'total_value': total_value,
            'currency': valuation_currency,
            'valuation_time': datetime.utcnow().isoformat(),
            'assets': assets if include_details else None
        }
        
        # Store the report
        self.reports[report_id] = {
            'id': report_id,
            'type': 'valuation',
            'data': valuation_data,
            'created_at': datetime.utcnow().isoformat()
        }
        
        return {
            'total_value': total_value,
            'currency': valuation_currency,
            'valuation_time': datetime.utcnow().isoformat(),
            'assets': assets,
            'report_url': f"/reports/{report_id}"
        }
    
    async def log_trade(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log a trade execution for performance tracking.
        
        Args:
            parameters: Parameters for the trade log
            
        Returns:
            Trade log status
        """
        self.logger.info(f"Logging trade: {parameters}")
        
        # Extract trade details
        order_id = parameters.get('order_id')
        exchange = parameters.get('exchange')
        crypto_pair = parameters.get('crypto_pair')
        action = parameters.get('action')
        order_type = parameters.get('order_type')
        quantity = parameters.get('quantity')
        executed_price = parameters.get('executed_price')
        timestamp = parameters.get('timestamp', datetime.utcnow().isoformat())
        
        # Validate required parameters
        if not order_id or not exchange or not crypto_pair or not action or not quantity or executed_price is None:
            raise ValueError("Missing required parameters for trade logging")
        
        # Create a trade record
        trade = {
            'order_id': order_id,
            'exchange': exchange,
            'crypto_pair': crypto_pair,
            'action': action,
            'order_type': order_type,
            'quantity': quantity,
            'executed_price': executed_price,
            'value': quantity * executed_price,
            'timestamp': timestamp,
            'recorded_at': datetime.utcnow().isoformat()
        }
        
        # Add to trades list
        self.trades.append(trade)
        
        # Update portfolio based on the trade
        self._update_portfolio_from_trade(trade)
        
        return {
            'status': 'success',
            'trade_id': order_id
        }
    
    def _calculate_total_return(self, trades: List[Dict[str, Any]]) -> tuple:
        """
        Calculate the total return from a list of trades.
        
        Args:
            trades: List of trade records
            
        Returns:
            Tuple of (total_return_value, total_return_percentage)
        """
        # For a proper implementation, this would require tracking portfolio value 
        # over time and calculating returns
        
        # For this prototype, we'll use a simplified approach
        # Assume that buys are negative cash flows and sells are positive cash flows
        total_investment = 0
        total_proceeds = 0
        
        for trade in trades:
            value = trade['quantity'] * trade['executed_price']
            if trade['action'] == 'buy':
                total_investment += value
            elif trade['action'] == 'sell':
                total_proceeds += value
        
        # Calculate profit/loss
        total_return = total_proceeds - total_investment
        
        # Calculate return percentage
        total_return_pct = total_return / total_investment if total_investment > 0 else 0
        
        return total_return, total_return_pct
    
    def _calculate_daily_returns(self, trades: List[Dict[str, Any]], start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Calculate daily returns from trade history.
        
        Args:
            trades: List of trade records
            start_date: Start date for calculations
            end_date: End date for calculations
            
        Returns:
            List of daily return data
        """
        # For a proper implementation, this would require tracking portfolio value 
        # day by day and calculating returns
        
        # For this prototype, we'll generate simulated daily returns
        days = (end_date - start_date).days + 1
        daily_returns = []
        
        # Seed the random generator for reproducibility
        np.random.seed(42)
        
        # Generate random daily returns with a slight upward bias
        simulated_returns = np.random.normal(0.001, 0.02, days)  # Mean 0.1%, std 2%
        
        current_date = start_date
        portfolio_value = 10000  # Assume starting portfolio value of $10k
        
        for i in range(days):
            daily_return = simulated_returns[i]
            portfolio_value *= (1 + daily_return)
            
            daily_returns.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'return': daily_return,
                'return_pct': daily_return * 100,
                'portfolio_value': portfolio_value
            })
            
            current_date += timedelta(days=1)
        
        return daily_returns
    
    def _calculate_max_drawdown(self, daily_returns: List[Dict[str, Any]]) -> float:
        """
        Calculate the maximum drawdown from daily return data.
        
        Args:
            daily_returns: List of daily return records
            
        Returns:
            Maximum drawdown as a decimal (not percentage)
        """
        if not daily_returns:
            return 0
        
        # Extract portfolio values
        portfolio_values = [day['portfolio_value'] for day in daily_returns]
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(portfolio_values)
        
        # Calculate drawdowns
        drawdowns = (running_max - portfolio_values) / running_max
        
        # Find maximum drawdown
        max_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else 0
        
        return max_drawdown
    
    def _calculate_sharpe_ratio(self, daily_returns: List[Dict[str, Any]], risk_free_rate: float = 0.02/365) -> float:
        """
        Calculate the Sharpe ratio from daily return data.
        
        Args:
            daily_returns: List of daily return records
            risk_free_rate: Daily risk-free rate (default: 2% annual / 365)
            
        Returns:
            Sharpe ratio
        """
        if not daily_returns:
            return 0
        
        # Extract daily returns
        returns = [day['return'] for day in daily_returns]
        
        # Calculate excess returns
        excess_returns = np.array(returns) - risk_free_rate
        
        # Calculate Sharpe ratio
        mean_excess_return = np.mean(excess_returns)
        std_excess_return = np.std(excess_returns)
        
        # Annualize the Sharpe ratio (multiply by sqrt(252) for daily returns)
        sharpe_ratio = (mean_excess_return / std_excess_return) * np.sqrt(252) if std_excess_return > 0 else 0
        
        return sharpe_ratio
    
    def _calculate_trade_statistics(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate trade statistics from a list of trades.
        
        Args:
            trades: List of trade records
            
        Returns:
            Trade statistics dictionary
        """
        if not trades:
            return {
                'total_trades': 0,
                'buy_trades': 0,
                'sell_trades': 0,
                'avg_trade_size': 0,
                'largest_trade': 0,
                'smallest_trade': 0
            }
        
        # Count trades by type
        buy_trades = [t for t in trades if t['action'] == 'buy']
        sell_trades = [t for t in trades if t['action'] == 'sell']
        
        # Calculate trade sizes
        trade_sizes = [t['value'] for t in trades]
        
        return {
            'total_trades': len(trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'avg_trade_size': sum(trade_sizes) / len(trades) if trades else 0,
            'largest_trade': max(trade_sizes) if trade_sizes else 0,
            'smallest_trade': min(trade_sizes) if trade_sizes else 0
        }
    
    def _get_current_portfolio(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the current portfolio state.
        In a real implementation, this would come from a database.
        
        Returns:
            Dictionary of portfolio positions
        """
        # For this prototype, we'll return a simulated portfolio
        if not self.portfolio:
            self.portfolio = {
                'BTC': {'quantity': 0.5, 'avg_price': 48000},
                'ETH': {'quantity': 5, 'avg_price': 2800},
                'SOL': {'quantity': 20, 'avg_price': 90},
                'ADA': {'quantity': 1000, 'avg_price': 0.8},
                'DOT': {'quantity': 100, 'avg_price': 18}
            }
        
        return self.portfolio
    
    def _update_portfolio_from_trade(self, trade: Dict[str, Any]) -> None:
        """
        Update the portfolio based on a trade execution.
        
        Args:
            trade: Trade record
        """
        crypto_pair = trade['crypto_pair']
        action = trade['action']
        quantity = trade['quantity']
        price = trade['executed_price']
        
        # Extract the base crypto from the trading pair (e.g., BTC from BTC/USD)
        crypto = crypto_pair.split('/')[0]
        
        # Update portfolio
        if action == 'buy':
            if crypto in self.portfolio:
                # Update existing position with weighted average price
                current_quantity = self.portfolio[crypto]['quantity']
                current_avg_price = self.portfolio[crypto]['avg_price']
                
                new_quantity = current_quantity + quantity
                new_avg_price = (current_quantity * current_avg_price + quantity * price) / new_quantity
                
                self.portfolio[crypto] = {
                    'quantity': new_quantity,
                    'avg_price': new_avg_price
                }
            else:
                # Add new position
                self.portfolio[crypto] = {
                    'quantity': quantity,
                    'avg_price': price
                }
        elif action == 'sell':
            if crypto in self.portfolio:
                current_quantity = self.portfolio[crypto]['quantity']
                
                # Update quantity
                new_quantity = current_quantity - quantity
                
                if new_quantity > 0:
                    # Just update the quantity
                    self.portfolio[crypto]['quantity'] = new_quantity
                else:
                    # Remove the position entirely
                    del self.portfolio[crypto]
    
    def _get_current_price(self, crypto: str) -> float:
        """
        Get the current price of a cryptocurrency.
        In a real implementation, this would fetch from market data.
        
        Args:
            crypto: The cryptocurrency
            
        Returns:
            Current price
        """
        # For this prototype, we'll use simplified price estimates
        base_prices = {
            'BTC': 50000,
            'ETH': 3000,
            'SOL': 100,
            'ADA': 1,
            'DOT': 20
        }
        
        return base_prices.get(crypto, 100)
    
    def _get_24h_price_change(self, crypto: str) -> float:
        """
        Get the 24-hour price change percentage of a cryptocurrency.
        In a real implementation, this would fetch from market data.
        
        Args:
            crypto: The cryptocurrency
            
        Returns:
            24-hour price change as a decimal (not percentage)
        """
        # For this prototype, we'll use simulated price changes
        simulated_changes = {
            'BTC': 0.05,  # 5% up
            'ETH': 0.08,  # 8% up
            'SOL': -0.03,  # 3% down
            'ADA': 0.02,  # 2% up
            'DOT': -0.01   # 1% down
        }
        
        return simulated_changes.get(crypto, 0)
    
    async def start(self, host: str = "0.0.0.0", port: int = 8004):
        """
        Start the Reporting and Analytics Agent.
        
        Args:
            host: Host to bind the server to
            port: Port to bind the server to
        """
        app = self.a2a_server.app
        
        # Add root endpoint for health checks
        @app.get("/")
        async def root():
            return {"status": "ok", "agent": self.name, "version": self.version}
        
        # Add reports endpoint
        @app.get("/reports/{report_id}")
        async def get_report(report_id: str):
            if report_id not in self.reports:
                return {"error": "Report not found"}, 404
            return self.reports[report_id]
        
        self.logger.info(f"Starting Reporting and Analytics Agent on {host}:{port}")
        
        # Start the server properly in async context
        config = uvicorn.Config(app, host=host, port=port)
        server = uvicorn.Server(config)
        await server.serve()


async def main():
    """Main entry point for the Reporting and Analytics Agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Start the Reporting and Analytics Agent')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind the server to')
    parser.add_argument('--port', type=int, default=8004, help='Port to bind the server to')
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
    agent = ReportingAnalyticsAgent(config_path=args.config)
    await agent.start(host=args.host, port=args.port)


if __name__ == "__main__":
    asyncio.run(main()) 