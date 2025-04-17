"""
Risk Management Agent for Smart Crypto Portfolio Manager

This agent monitors the portfolio's overall risk exposure, assesses risk associated with
potential trades, and triggers actions to mitigate risk.
"""

import os
import json
import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

import uvicorn
from fastapi import FastAPI

# Import the A2A server implementation
import sys
# Use relative import path instead of hardcoded path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from a2a.server import create_a2a_server
from a2a.client import A2AClient


class RiskManagementAgent:
    """
    Agent for monitoring and managing cryptocurrency portfolio risk.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the Risk Management Agent.
        
        Args:
            config_path: Path to the configuration file (optional)
        """
        self.name = "Risk Management Agent"
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
        self.a2a_server.register_capability_handler('assess_trade_risk', self.assess_trade_risk)
        self.a2a_server.register_capability_handler('monitor_portfolio_risk', self.monitor_portfolio_risk)
        self.a2a_server.register_capability_handler('update_portfolio', self.update_portfolio)
        
        # Initialize portfolio data
        self.portfolio = {}
        self.portfolio_history = []
        self.risk_metrics = {}
        
        # Load initial portfolio data if available
        self._load_portfolio()
        
        # Risk thresholds
        self.risk_thresholds = self.config.get('risk_thresholds', {
            'value_at_risk': 0.05,  # 5% VaR
            'exposure_per_asset': 0.25,  # 25% max exposure per asset
            'total_exposure': 0.75,  # 75% max total exposure
            'volatility': 0.02,  # 2% daily volatility
            'correlation': 0.8  # 0.8 correlation threshold
        })
    
    def _load_portfolio(self):
        """
        Load initial portfolio data.
        In a real implementation, this would load from a database or storage service.
        """
        # For this prototype, we'll initialize with an empty portfolio
        # or load from a predefined configuration
        initial_holdings = self.config.get('initial_holdings', [])
        for holding in initial_holdings:
            crypto = holding.get('crypto')
            quantity = holding.get('quantity', 0)
            avg_price = holding.get('avg_price', 0)
            
            if crypto and quantity > 0:
                self.portfolio[crypto] = {
                    'quantity': quantity,
                    'avg_price': avg_price,
                    'last_updated': datetime.utcnow().isoformat()
                }
    
    async def assess_trade_risk(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess the risk of a proposed trade in the context of the current portfolio.
        
        Args:
            parameters: Parameters for the risk assessment
            
        Returns:
            Risk assessment results
        """
        self.logger.info(f"Assessing trade risk: {parameters}")
        
        # Extract parameters
        crypto_pair = parameters.get('crypto_pair')
        action = parameters.get('action')
        quantity = parameters.get('quantity')
        price = parameters.get('price')
        
        # Validate required parameters
        if not crypto_pair or not action or quantity is None or price is None:
            raise ValueError("Missing required parameters for risk assessment")
        
        # Extract the base crypto from the trading pair (e.g., BTC from BTC/USD)
        crypto = crypto_pair.split('/')[0]
        
        # Calculate the trade value
        trade_value = quantity * price
        
        # Assess risk factors
        
        # 1. Check portfolio concentration risk
        concentration_risk, max_recommended_quantity = self._assess_concentration_risk(
            crypto, quantity, price, action
        )
        
        # 2. Check volatility risk
        volatility_risk = self._assess_volatility_risk(crypto)
        
        # 3. Check correlation risk
        correlation_risk = self._assess_correlation_risk(crypto)
        
        # 4. Determine overall risk score
        risk_score = (
            concentration_risk * 0.5 +  # 50% weight on concentration
            volatility_risk * 0.3 +     # 30% weight on volatility
            correlation_risk * 0.2      # 20% weight on correlation
        ) * 100  # Scale to 0-100
        
        # Determine approval based on risk score threshold
        approval = risk_score < 70  # Approve if risk score is less than 70
        
        # Prepare reasons
        reasons = []
        if concentration_risk > 0.7:
            reasons.append(f"High concentration risk: Trade would result in significant portfolio exposure to {crypto}")
        if volatility_risk > 0.7:
            reasons.append(f"High volatility risk: {crypto} has shown significant price volatility")
        if correlation_risk > 0.7:
            reasons.append(f"High correlation risk: {crypto} is highly correlated with other assets in the portfolio")
        
        if not reasons:
            reasons.append("Trade is within acceptable risk parameters")
        
        return {
            'risk_score': risk_score,
            'approval': approval,
            'max_recommended_quantity': max_recommended_quantity,
            'reasons': reasons
        }
    
    async def monitor_portfolio_risk(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Monitor the overall portfolio risk and generate alerts if thresholds are exceeded.
        
        Args:
            parameters: Parameters for the risk monitoring
            
        Returns:
            Portfolio risk assessment
        """
        self.logger.info(f"Monitoring portfolio risk: {parameters}")
        
        # Extract parameters
        metrics = parameters.get('metrics', ['value_at_risk', 'exposure', 'volatility', 'correlation'])
        threshold_overrides = parameters.get('threshold_overrides', {})
        
        # Apply threshold overrides
        thresholds = self.risk_thresholds.copy()
        thresholds.update(threshold_overrides)
        
        # Calculate risk metrics
        risk_metrics = {}
        alerts = []
        
        # Value at Risk (VaR)
        if 'value_at_risk' in metrics:
            var = self._calculate_value_at_risk()
            risk_metrics['value_at_risk'] = var
            
            if var > thresholds['value_at_risk']:
                alerts.append({
                    'metric': 'value_at_risk',
                    'value': var,
                    'threshold': thresholds['value_at_risk'],
                    'recommendation': "Consider reducing exposure or adding hedging positions"
                })
        
        # Exposure metrics
        if 'exposure' in metrics:
            # Calculate per-asset exposure
            total_value = self._calculate_portfolio_value()
            exposures = {}
            
            for crypto, details in self.portfolio.items():
                # In a real implementation, get the current price from market data
                current_price = self._get_current_price(crypto)
                value = details['quantity'] * current_price
                exposure = value / total_value if total_value > 0 else 0
                exposures[crypto] = exposure
                
                if exposure > thresholds['exposure_per_asset']:
                    alerts.append({
                        'metric': f'exposure_{crypto}',
                        'value': exposure,
                        'threshold': thresholds['exposure_per_asset'],
                        'recommendation': f"Consider reducing {crypto} position to rebalance portfolio"
                    })
            
            # Calculate total exposure
            total_exposure = sum(exposures.values())
            risk_metrics['total_exposure'] = total_exposure
            risk_metrics['exposures'] = exposures
            
            if total_exposure > thresholds['total_exposure']:
                alerts.append({
                    'metric': 'total_exposure',
                    'value': total_exposure,
                    'threshold': thresholds['total_exposure'],
                    'recommendation': "Consider moving some assets to stable reserves"
                })
        
        # Volatility
        if 'volatility' in metrics:
            portfolio_volatility = self._calculate_portfolio_volatility()
            risk_metrics['volatility'] = portfolio_volatility
            
            if portfolio_volatility > thresholds['volatility']:
                alerts.append({
                    'metric': 'volatility',
                    'value': portfolio_volatility,
                    'threshold': thresholds['volatility'],
                    'recommendation': "Consider adding less volatile assets to reduce overall portfolio volatility"
                })
        
        # Correlation
        if 'correlation' in metrics:
            # In a real implementation, we would calculate a correlation matrix
            # For this prototype, we'll skip the actual calculation
            risk_metrics['correlation'] = 0.5  # Placeholder
        
        # Determine overall risk level
        overall_risk_level = 'low'
        if len(alerts) >= 3:
            overall_risk_level = 'extreme'
        elif len(alerts) == 2:
            overall_risk_level = 'high'
        elif len(alerts) == 1:
            overall_risk_level = 'medium'
        
        return {
            'overall_risk_level': overall_risk_level,
            'metrics': risk_metrics,
            'alerts': alerts
        }
    
    async def update_portfolio(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the portfolio with a new trade execution.
        
        Args:
            parameters: Parameters for the portfolio update
            
        Returns:
            Update status
        """
        self.logger.info(f"Updating portfolio: {parameters}")
        
        # Extract parameters
        crypto_pair = parameters.get('crypto_pair')
        action = parameters.get('action')
        quantity = parameters.get('quantity')
        executed_price = parameters.get('executed_price')
        
        # Validate required parameters
        if not crypto_pair or not action or quantity is None or executed_price is None:
            raise ValueError("Missing required parameters for portfolio update")
        
        # Extract the base crypto from the trading pair (e.g., BTC from BTC/USD)
        crypto = crypto_pair.split('/')[0]
        
        # Update portfolio with the new trade
        timestamp = datetime.utcnow().isoformat()
        
        if action == 'buy':
            if crypto in self.portfolio:
                # Update existing position with weighted average price
                current_quantity = self.portfolio[crypto]['quantity']
                current_avg_price = self.portfolio[crypto]['avg_price']
                
                new_quantity = current_quantity + quantity
                new_avg_price = (current_quantity * current_avg_price + quantity * executed_price) / new_quantity
                
                self.portfolio[crypto] = {
                    'quantity': new_quantity,
                    'avg_price': new_avg_price,
                    'last_updated': timestamp
                }
            else:
                # Add new position
                self.portfolio[crypto] = {
                    'quantity': quantity,
                    'avg_price': executed_price,
                    'last_updated': timestamp
                }
        elif action == 'sell':
            if crypto not in self.portfolio:
                raise ValueError(f"Cannot sell {crypto}: not in portfolio")
            
            current_quantity = self.portfolio[crypto]['quantity']
            
            if quantity > current_quantity:
                raise ValueError(f"Cannot sell {quantity} {crypto}: only have {current_quantity}")
            
            # Update quantity
            new_quantity = current_quantity - quantity
            
            if new_quantity > 0:
                # Just update the quantity
                self.portfolio[crypto]['quantity'] = new_quantity
                self.portfolio[crypto]['last_updated'] = timestamp
            else:
                # Remove the position entirely
                del self.portfolio[crypto]
        
        # Add to portfolio history
        self.portfolio_history.append({
            'timestamp': timestamp,
            'action': action,
            'crypto': crypto,
            'quantity': quantity,
            'price': executed_price,
            'portfolio': self.portfolio.copy()
        })
        
        # Update risk metrics
        self._update_risk_metrics()
        
        return {
            'status': 'success',
            'portfolio': self.portfolio,
            'timestamp': timestamp
        }
    
    def _assess_concentration_risk(self, crypto: str, quantity: float, price: float, action: str) -> Tuple[float, float]:
        """
        Assess the concentration risk of a proposed trade.
        
        Args:
            crypto: The cryptocurrency
            quantity: The quantity to trade
            price: The expected price
            action: Buy or sell
            
        Returns:
            Tuple of (risk_score, max_recommended_quantity)
        """
        # Calculate the current portfolio value
        total_value = self._calculate_portfolio_value()
        
        # Calculate the value of the proposed trade
        trade_value = quantity * price
        
        # Calculate the current exposure to this crypto
        current_exposure = 0
        if crypto in self.portfolio:
            current_price = self._get_current_price(crypto)
            current_value = self.portfolio[crypto]['quantity'] * current_price
            current_exposure = current_value / total_value if total_value > 0 else 0
        
        # Calculate the new exposure after the trade
        new_total_value = total_value
        new_crypto_value = 0
        
        if action == 'buy':
            new_total_value = total_value + trade_value
            new_crypto_value = (self.portfolio.get(crypto, {}).get('quantity', 0) + quantity) * price
        elif action == 'sell':
            new_total_value = total_value - trade_value
            new_crypto_value = (self.portfolio.get(crypto, {}).get('quantity', 0) - quantity) * price
        
        new_exposure = new_crypto_value / new_total_value if new_total_value > 0 else 0
        
        # Calculate the concentration risk score (0-1, higher is more risky)
        risk_score = min(new_exposure / self.risk_thresholds['exposure_per_asset'], 1.0)
        
        # Calculate the maximum recommended quantity
        max_exposure = self.risk_thresholds['exposure_per_asset']
        max_value = max_exposure * total_value
        
        if action == 'buy':
            current_value = self.portfolio.get(crypto, {}).get('quantity', 0) * price
            max_additional_value = max(max_value - current_value, 0)
            max_recommended_quantity = max_additional_value / price if price > 0 else 0
        else:
            # For selling, no concentration issue
            max_recommended_quantity = self.portfolio.get(crypto, {}).get('quantity', 0)
        
        return risk_score, max_recommended_quantity
    
    def _assess_volatility_risk(self, crypto: str) -> float:
        """
        Assess the volatility risk of a cryptocurrency.
        
        Args:
            crypto: The cryptocurrency
            
        Returns:
            Volatility risk score (0-1, higher is more risky)
        """
        # In a real implementation, we would calculate historical volatility
        # For this prototype, we'll use a simplified approach
        
        # These are just simulated volatility values
        simulated_volatilities = {
            'BTC': 0.03,  # 3% daily volatility
            'ETH': 0.04,
            'SOL': 0.06,
            'ADA': 0.05,
            'DOT': 0.07
        }
        
        volatility = simulated_volatilities.get(crypto, 0.05)
        
        # Calculate the risk score based on volatility
        risk_score = min(volatility / self.risk_thresholds['volatility'], 1.0)
        
        return risk_score
    
    def _assess_correlation_risk(self, crypto: str) -> float:
        """
        Assess the correlation risk of a cryptocurrency with the existing portfolio.
        
        Args:
            crypto: The cryptocurrency
            
        Returns:
            Correlation risk score (0-1, higher is more risky)
        """
        # In a real implementation, we would calculate correlation with existing assets
        # For this prototype, we'll use a simplified approach
        
        # These are just simulated correlation values
        simulated_correlations = {
            'BTC': {'ETH': 0.7, 'SOL': 0.5, 'ADA': 0.4, 'DOT': 0.6},
            'ETH': {'BTC': 0.7, 'SOL': 0.6, 'ADA': 0.5, 'DOT': 0.7},
            'SOL': {'BTC': 0.5, 'ETH': 0.6, 'ADA': 0.7, 'DOT': 0.5},
            'ADA': {'BTC': 0.4, 'ETH': 0.5, 'SOL': 0.7, 'DOT': 0.8},
            'DOT': {'BTC': 0.6, 'ETH': 0.7, 'SOL': 0.5, 'ADA': 0.8}
        }
        
        # Calculate the average correlation with assets in the portfolio
        correlations = []
        
        for existing_crypto in self.portfolio:
            if existing_crypto != crypto and crypto in simulated_correlations:
                correlation = simulated_correlations.get(crypto, {}).get(existing_crypto, 0.5)
                correlations.append(correlation)
        
        avg_correlation = sum(correlations) / len(correlations) if correlations else 0
        
        # Calculate the risk score based on correlation
        risk_score = min(avg_correlation / self.risk_thresholds['correlation'], 1.0)
        
        return risk_score
    
    def _calculate_value_at_risk(self) -> float:
        """
        Calculate the Value at Risk (VaR) for the portfolio.
        
        Returns:
            Value at Risk as a percentage of portfolio value
        """
        # In a real implementation, this would use historical price data
        # and calculate VaR using statistical methods
        
        # For this prototype, we'll use a simplified approach
        total_value = self._calculate_portfolio_value()
        
        # Calculate a weighted average of asset volatilities
        weighted_volatility = 0
        
        for crypto, details in self.portfolio.items():
            current_price = self._get_current_price(crypto)
            value = details['quantity'] * current_price
            weight = value / total_value if total_value > 0 else 0
            
            # Get volatility for this asset
            volatility = self._assess_volatility_risk(crypto) * self.risk_thresholds['volatility']
            weighted_volatility += weight * volatility
        
        # Simplified VaR calculation (assuming normal distribution, 95% confidence)
        var = 1.645 * weighted_volatility
        
        return var
    
    def _calculate_portfolio_value(self) -> float:
        """
        Calculate the total value of the portfolio.
        
        Returns:
            Total portfolio value
        """
        total_value = 0
        
        for crypto, details in self.portfolio.items():
            current_price = self._get_current_price(crypto)
            value = details['quantity'] * current_price
            total_value += value
        
        return total_value
    
    def _calculate_portfolio_volatility(self) -> float:
        """
        Calculate the overall volatility of the portfolio.
        
        Returns:
            Portfolio volatility
        """
        # In a real implementation, this would use historical returns
        # and calculate the standard deviation
        
        # For this prototype, we'll use a simplified approach
        total_value = self._calculate_portfolio_value()
        
        # Calculate a weighted average of asset volatilities
        weighted_volatility = 0
        
        for crypto, details in self.portfolio.items():
            current_price = self._get_current_price(crypto)
            value = details['quantity'] * current_price
            weight = value / total_value if total_value > 0 else 0
            
            # Get volatility for this asset
            volatility = self._assess_volatility_risk(crypto) * self.risk_thresholds['volatility']
            weighted_volatility += weight * volatility
        
        return weighted_volatility
    
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
    
    def _update_risk_metrics(self):
        """
        Update all risk metrics for the portfolio.
        """
        self.risk_metrics = {
            'value_at_risk': self._calculate_value_at_risk(),
            'portfolio_value': self._calculate_portfolio_value(),
            'volatility': self._calculate_portfolio_volatility(),
            'updated_at': datetime.utcnow().isoformat()
        }
    
    async def start(self, host: str = "0.0.0.0", port: int = 8003):
        """
        Start the Risk Management Agent.
        
        Args:
            host: Host to bind the server to
            port: Port to bind the server to
        """
        app = self.a2a_server.app
        
        # Add root endpoint for health checks
        @app.get("/")
        async def root():
            return {"status": "ok", "agent": self.name, "version": self.version}
        
        self.logger.info(f"Starting Risk Management Agent on {host}:{port}")
        
        # Start a background task to periodically monitor risk
        # This would be implemented in a real system
        
        # Start the server properly in async context
        config = uvicorn.Config(app, host=host, port=port)
        server = uvicorn.Server(config)
        await server.serve()


async def main():
    """Main entry point for the Risk Management Agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Start the Risk Management Agent')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind the server to')
    parser.add_argument('--port', type=int, default=8003, help='Port to bind the server to')
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
    agent = RiskManagementAgent(config_path=args.config)
    await agent.start(host=args.host, port=args.port)


if __name__ == "__main__":
    asyncio.run(main()) 