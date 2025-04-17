"""
Risk Management Agent for Smart Crypto Portfolio Manager

This agent monitors portfolio risk exposure, assesses risks of potential trades,
and suggests risk mitigation actions.
"""

import os
import json
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

import uvicorn
import numpy as np
import pandas as pd
from fastapi import FastAPI

# Import the A2A server implementation
import sys
# Use relative import path instead of hardcoded path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from a2a.server import create_a2a_server
from a2a.client import A2AClient


class RiskManagementAgent:
    """Agent for monitoring and managing portfolio risk."""
    
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
        
        # Initialize in-memory portfolio data
        self.portfolio = self._initialize_portfolio()
        self.price_history = {}
        self.trade_history = []
        
        # Load risk settings from configuration
        self.risk_settings = self.config.get('portfolio', {})
    
    def _initialize_portfolio(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize an empty portfolio structure.
        
        Returns:
            Dictionary with portfolio data
        """
        return {
            "assets": {},
            "total_value_usd": 0,
            "cash_usd": 100000,  # Starting with $100k in cash
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def assess_trade_risk(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess the risk of a proposed trade based on current portfolio exposure.
        
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
            raise ValueError("Missing required parameters for trade risk assessment")
        
        # Parse asset from trading pair (e.g., 'BTC/USD' -> 'BTC')
        asset = crypto_pair.split('/')[0]
        
        # Calculate trade value in USD
        trade_value_usd = quantity * price
        
        # Calculate current portfolio exposure
        current_exposure = self._calculate_asset_exposure(asset)
        
        # Calculate new exposure after the trade
        new_exposure = self._calculate_new_exposure(asset, action, trade_value_usd)
        
        # Calculate risk score based on multiple factors
        risk_score, reasons = self._calculate_risk_score(asset, action, quantity, price, new_exposure)
        
        # Determine if the trade is approved based on risk score
        approval = risk_score < 70  # Approve trades with risk score below 70
        
        # Calculate maximum recommended quantity to maintain acceptable risk
        max_recommended_quantity = self._calculate_max_recommended_quantity(
            asset, action, price, risk_score
        )
        
        return {
            "risk_score": risk_score,
            "approval": approval,
            "max_recommended_quantity": max_recommended_quantity,
            "reasons": reasons
        }
    
    async def monitor_portfolio_risk(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Monitor the overall portfolio risk and return risk metrics.
        
        Args:
            parameters: Parameters for the risk monitoring
            
        Returns:
            Risk monitoring results
        """
        self.logger.info(f"Monitoring portfolio risk: {parameters}")
        
        # Extract parameters
        metrics = parameters.get('metrics', [
            'var', 'exposure', 'correlation', 'volatility', 'sharpe_ratio'
        ])
        
        # Calculate requested metrics
        metrics_results = {}
        alerts = []
        
        # Calculate Value at Risk (VaR)
        if 'var' in metrics:
            var_value = self._calculate_value_at_risk()
            metrics_results['var'] = var_value
            
            # Check if VaR exceeds threshold
            var_threshold = self.risk_settings.get('var', {}).get('threshold', 0.05)
            if var_value > var_threshold:
                alerts.append({
                    "metric": "var",
                    "value": var_value,
                    "threshold": var_threshold,
                    "recommendation": "Consider reducing position sizes or hedging"
                })
        
        # Calculate portfolio exposure
        if 'exposure' in metrics:
            exposure = self._calculate_portfolio_exposure()
            metrics_results['exposure'] = exposure
            
            # Check if exposure exceeds threshold
            max_exposure = self.risk_settings.get('max_exposure_percent', {}).get('total', 80)
            if exposure > max_exposure:
                alerts.append({
                    "metric": "exposure",
                    "value": exposure,
                    "threshold": max_exposure,
                    "recommendation": "Reduce exposure by taking profits or selling some assets"
                })
        
        # Calculate asset correlation
        if 'correlation' in metrics:
            correlation = self._calculate_asset_correlation()
            metrics_results['correlation'] = correlation
            
            # Check if correlation exceeds threshold
            corr_threshold = self.risk_settings.get('diversification', {}).get(
                'asset_correlation_threshold', 0.7
            )
            if correlation > corr_threshold:
                alerts.append({
                    "metric": "correlation",
                    "value": correlation,
                    "threshold": corr_threshold,
                    "recommendation": "Increase diversification by adding uncorrelated assets"
                })
        
        # Calculate portfolio volatility
        if 'volatility' in metrics:
            volatility = self._calculate_portfolio_volatility()
            metrics_results['volatility'] = volatility
            
            # Check if volatility exceeds threshold
            vol_threshold = self.risk_settings.get('market_risk', {}).get('volatility_threshold', 0.3)
            if volatility > vol_threshold:
                alerts.append({
                    "metric": "volatility",
                    "value": volatility,
                    "threshold": vol_threshold,
                    "recommendation": "Consider reducing positions in high-volatility assets"
                })
        
        # Calculate Sharpe Ratio
        if 'sharpe_ratio' in metrics:
            sharpe = self._calculate_sharpe_ratio()
            metrics_results['sharpe_ratio'] = sharpe
            
            # Check if Sharpe Ratio is below threshold
            sharpe_threshold = 1.0  # Generally, Sharpe Ratio > 1 is considered good
            if sharpe < sharpe_threshold:
                alerts.append({
                    "metric": "sharpe_ratio",
                    "value": sharpe,
                    "threshold": sharpe_threshold,
                    "recommendation": "Optimize portfolio for better risk-adjusted returns"
                })
        
        # Determine overall risk level based on alerts
        risk_level = self._determine_risk_level(metrics_results, alerts)
        
        return {
            "risk_level": risk_level,
            "metrics": metrics_results,
            "alerts": alerts
        }
    
    async def update_portfolio(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the portfolio data with a new trade.
        
        Args:
            parameters: Parameters for the portfolio update
            
        Returns:
            Update results
        """
        self.logger.info(f"Updating portfolio with trade: {parameters}")
        
        # Extract parameters
        order_id = parameters.get('order_id')
        exchange = parameters.get('exchange')
        crypto_pair = parameters.get('crypto_pair')
        action = parameters.get('action')
        quantity = parameters.get('quantity')
        executed_price = parameters.get('executed_price')
        
        # Validate required parameters
        if not all([order_id, exchange, crypto_pair, action, quantity, executed_price]):
            raise ValueError("Missing required parameters for portfolio update")
        
        # Parse asset from trading pair (e.g., 'BTC/USD' -> 'BTC')
        asset = crypto_pair.split('/')[0]
        
        # Calculate trade value in USD
        trade_value_usd = quantity * executed_price
        
        # Update portfolio data
        if asset not in self.portfolio['assets']:
            self.portfolio['assets'][asset] = {
                "quantity": 0,
                "value_usd": 0,
                "avg_price": 0
            }
        
        # Update asset quantity and value based on action
        if action == 'buy':
            # Calculate new average price
            current_quantity = self.portfolio['assets'][asset]["quantity"]
            current_value = self.portfolio['assets'][asset]["value_usd"]
            
            new_quantity = current_quantity + quantity
            new_value = current_value + trade_value_usd
            
            if new_quantity > 0:
                new_avg_price = new_value / new_quantity
            else:
                new_avg_price = executed_price
            
            # Update asset data
            self.portfolio['assets'][asset]["quantity"] = new_quantity
            self.portfolio['assets'][asset]["value_usd"] = new_value
            self.portfolio['assets'][asset]["avg_price"] = new_avg_price
            
            # Deduct cash for the purchase
            self.portfolio['cash_usd'] -= trade_value_usd
            
        elif action == 'sell':
            # Calculate remaining quantity and value
            current_quantity = self.portfolio['assets'][asset]["quantity"]
            current_value = self.portfolio['assets'][asset]["value_usd"]
            current_avg_price = self.portfolio['assets'][asset]["avg_price"]
            
            # Check if we have enough to sell
            if current_quantity < quantity:
                self.logger.warning(f"Selling more {asset} than in portfolio!")
                actual_quantity = current_quantity
            else:
                actual_quantity = quantity
            
            # Calculate new values
            new_quantity = current_quantity - actual_quantity
            
            # Calculate the value reduction proportionally from the average price
            value_reduction = actual_quantity * current_avg_price
            new_value = current_value - value_reduction
            
            if new_quantity > 0:
                new_avg_price = current_avg_price  # Keep the same average price
            else:
                new_avg_price = 0
            
            # Update asset data
            self.portfolio['assets'][asset]["quantity"] = new_quantity
            self.portfolio['assets'][asset]["value_usd"] = new_value
            self.portfolio['assets'][asset]["avg_price"] = new_avg_price
            
            # Add cash from the sale
            self.portfolio['cash_usd'] += actual_quantity * executed_price
        
        # Update total portfolio value
        self.portfolio['total_value_usd'] = self._calculate_total_portfolio_value()
        
        # Update timestamp
        self.portfolio['last_updated'] = datetime.utcnow().isoformat()
        
        # Add to trade history
        self.trade_history.append({
            "order_id": order_id,
            "exchange": exchange,
            "crypto_pair": crypto_pair,
            "action": action,
            "quantity": quantity,
            "executed_price": executed_price,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Check new risk level
        risk_monitoring_result = await self.monitor_portfolio_risk({"metrics": ["var", "exposure"]})
        new_risk_level = risk_monitoring_result.get("risk_level", "medium")
        
        # Trigger emergency protocols if risk is extreme
        if new_risk_level == "extreme":
            await self._trigger_emergency_protocols()
        
        return {
            "success": True,
            "new_risk_level": new_risk_level
        }
    
    def _calculate_asset_exposure(self, asset: str) -> float:
        """
        Calculate the current exposure to a specific asset as a percentage of portfolio.
        
        Args:
            asset: The asset to calculate exposure for
            
        Returns:
            Exposure as a percentage (0-100)
        """
        # Get total portfolio value
        total_value = self.portfolio['total_value_usd']
        if total_value == 0:
            return 0
        
        # Get asset value
        asset_value = self.portfolio['assets'].get(asset, {}).get('value_usd', 0)
        
        # Calculate exposure percentage
        exposure = (asset_value / total_value) * 100
        
        return exposure
    
    def _calculate_new_exposure(self, asset: str, action: str, trade_value_usd: float) -> float:
        """
        Calculate the new exposure to an asset after a potential trade.
        
        Args:
            asset: The asset to calculate exposure for
            action: Whether the trade is a buy or sell
            trade_value_usd: The value of the trade in USD
            
        Returns:
            New exposure as a percentage (0-100)
        """
        # Get current asset value
        current_asset_value = self.portfolio['assets'].get(asset, {}).get('value_usd', 0)
        
        # Calculate new asset value based on action
        if action == 'buy':
            new_asset_value = current_asset_value + trade_value_usd
        else:  # sell
            new_asset_value = current_asset_value - trade_value_usd
            new_asset_value = max(0, new_asset_value)  # Cannot be negative
        
        # Calculate new total portfolio value
        current_total_value = self.portfolio['total_value_usd']
        new_total_value = current_total_value  # Total value doesn't change for buy/sell
        
        if new_total_value == 0:
            return 0
        
        # Calculate new exposure percentage
        new_exposure = (new_asset_value / new_total_value) * 100
        
        return new_exposure
    
    def _calculate_risk_score(
        self, asset: str, action: str, quantity: float, price: float, new_exposure: float
    ) -> Tuple[float, List[str]]:
        """
        Calculate a risk score (0-100) for a proposed trade based on multiple factors.
        
        Args:
            asset: The asset being traded
            action: Whether the trade is a buy or sell
            quantity: The quantity to trade
            price: The execution price
            new_exposure: The new exposure to the asset after the trade
            
        Returns:
            Tuple of (risk_score, reasons)
        """
        reasons = []
        risk_factors = []
        
        # Factor 1: Exposure risk
        max_exposure = self.risk_settings.get('max_exposure_percent', {}).get(
            'per_asset', {}).get(asset, 10
        )
        
        exposure_risk = (new_exposure / max_exposure) * 50
        risk_factors.append(exposure_risk)
        
        if new_exposure > max_exposure:
            reasons.append(f"Exposure to {asset} ({new_exposure:.2f}%) exceeds maximum ({max_exposure}%)")
        
        # Factor 2: Asset volatility risk
        volatility = self._get_asset_volatility(asset)
        volatility_risk = volatility * 100
        risk_factors.append(volatility_risk)
        
        if volatility > 0.3:
            reasons.append(f"{asset} has high volatility ({volatility:.2f})")
        
        # Factor 3: Market correlation risk
        correlation = self._get_asset_correlation(asset)
        correlation_risk = correlation * 50
        risk_factors.append(correlation_risk)
        
        if correlation > 0.7:
            reasons.append(f"{asset} has high correlation with portfolio ({correlation:.2f})")
        
        # Factor 4: Order size risk
        total_value = self.portfolio['total_value_usd']
        if total_value == 0:
            order_size_risk = 0
        else:
            order_size_pct = (quantity * price / total_value) * 100
            order_size_risk = min(order_size_pct * 5, 100)
            
            if order_size_pct > 10:
                reasons.append(f"Order size ({order_size_pct:.2f}% of portfolio) is large")
        
        risk_factors.append(order_size_risk)
        
        # Calculate final risk score (weighted average of risk factors)
        weights = [0.4, 0.3, 0.2, 0.1]  # Weights for each risk factor
        risk_score = sum(score * weight for score, weight in zip(risk_factors, weights))
        
        # Reduce risk score for sell orders (selling reduces risk)
        if action == 'sell':
            risk_score = max(0, risk_score - 20)
            reasons.append("Selling reduces overall portfolio risk")
        
        # Add an overall assessment
        if risk_score < 30:
            reasons.append("Overall risk is low")
        elif risk_score < 60:
            reasons.append("Overall risk is moderate")
        else:
            reasons.append("Overall risk is high")
        
        return min(risk_score, 100), reasons
    
    def _calculate_max_recommended_quantity(
        self, asset: str, action: str, price: float, risk_score: float
    ) -> float:
        """
        Calculate the maximum recommended quantity to maintain acceptable risk levels.
        
        Args:
            asset: The asset being traded
            action: Whether the trade is a buy or sell
            price: The execution price
            risk_score: The calculated risk score
            
        Returns:
            Maximum recommended quantity
        """
        if action == 'sell':
            # For selling, the max quantity is what we have
            current_quantity = self.portfolio['assets'].get(asset, {}).get('quantity', 0)
            return current_quantity
        
        # For buying, calculate max quantity based on max exposure
        total_value = self.portfolio['total_value_usd']
        max_exposure_pct = self.risk_settings.get('max_exposure_percent', {}).get(
            'per_asset', {}).get(asset, 10
        )
        
        # Adjust max exposure based on risk score
        if risk_score > 70:
            max_exposure_pct = max_exposure_pct * 0.7
        elif risk_score > 50:
            max_exposure_pct = max_exposure_pct * 0.9
        
        # Calculate max value
        max_value = (max_exposure_pct / 100) * total_value
        
        # Subtract current value
        current_value = self.portfolio['assets'].get(asset, {}).get('value_usd', 0)
        max_additional_value = max_value - current_value
        
        # Calculate max quantity
        if price == 0:
            return 0
        
        max_quantity = max_additional_value / price
        
        # Ensure it's not negative
        return max(0, max_quantity)
    
    def _calculate_total_portfolio_value(self) -> float:
        """
        Calculate the total value of the portfolio in USD.
        
        Returns:
            Total portfolio value in USD
        """
        asset_values = sum(asset['value_usd'] for asset in self.portfolio['assets'].values())
        cash = self.portfolio['cash_usd']
        return asset_values + cash
    
    def _calculate_portfolio_exposure(self) -> float:
        """
        Calculate the overall portfolio exposure to crypto assets as a percentage.
        
        Returns:
            Portfolio exposure (0-100)
        """
        total_value = self.portfolio['total_value_usd']
        if total_value == 0:
            return 0
        
        asset_values = sum(asset['value_usd'] for asset in self.portfolio['assets'].values())
        exposure = (asset_values / total_value) * 100
        return exposure
    
    def _calculate_value_at_risk(self) -> float:
        """
        Calculate the Value at Risk (VaR) for the portfolio.
        
        Returns:
            Value at Risk as a percentage of portfolio value
        """
        # In a real implementation, this would use historical price data
        # For simulation, we'll return a simplified VaR based on portfolio composition
        
        # Get portfolio volatility
        portfolio_volatility = self._calculate_portfolio_volatility()
        
        # Calculate VaR (95% confidence)
        confidence_factor = 1.65  # Approximately 95% confidence for normal distribution
        var = portfolio_volatility * confidence_factor
        
        return var
    
    def _calculate_portfolio_volatility(self) -> float:
        """
        Calculate the volatility of the portfolio.
        
        Returns:
            Portfolio volatility (0-1)
        """
        # In a real implementation, this would use historical price data
        # For simulation, we'll calculate a weighted average of asset volatilities
        total_value = self.portfolio['total_value_usd']
        if total_value == 0:
            return 0.05  # Default low volatility
        
        weighted_volatility = 0
        for asset, data in self.portfolio['assets'].items():
            asset_volatility = self._get_asset_volatility(asset)
            weight = data['value_usd'] / total_value
            weighted_volatility += asset_volatility * weight
        
        return weighted_volatility
    
    def _get_asset_volatility(self, asset: str) -> float:
        """
        Get the volatility of a specific asset.
        
        Args:
            asset: The asset to get volatility for
            
        Returns:
            Asset volatility (0-1)
        """
        # In a real implementation, this would use historical price data
        # For simulation, we'll use some predefined values or generate them
        volatility_map = {
            'BTC': 0.25,
            'ETH': 0.30,
            'SOL': 0.40,
            'ADA': 0.35,
            'DOT': 0.38
        }
        
        return volatility_map.get(asset, 0.35)  # Default to 0.35
    
    def _calculate_asset_correlation(self) -> float:
        """
        Calculate the average correlation between assets in the portfolio.
        
        Returns:
            Average correlation (0-1)
        """
        # In a real implementation, this would use historical price data
        # For simulation, we'll return a fixed value
        return 0.6  # Moderate correlation
    
    def _get_asset_correlation(self, asset: str) -> float:
        """
        Get the correlation of an asset with the rest of the portfolio.
        
        Args:
            asset: The asset to get correlation for
            
        Returns:
            Correlation (0-1)
        """
        # In a real implementation, this would use historical price data
        # For simulation, we'll use some predefined values
        correlation_map = {
            'BTC': 0.7,
            'ETH': 0.75,
            'SOL': 0.65,
            'ADA': 0.6,
            'DOT': 0.65
        }
        
        return correlation_map.get(asset, 0.6)  # Default to 0.6
    
    def _calculate_sharpe_ratio(self) -> float:
        """
        Calculate the Sharpe Ratio for the portfolio.
        
        Returns:
            Sharpe Ratio
        """
        # In a real implementation, this would use historical returns
        # For simulation, we'll return a fixed value
        return 1.2  # Decent Sharpe Ratio
    
    def _determine_risk_level(self, metrics: Dict[str, float], alerts: List[Dict[str, Any]]) -> str:
        """
        Determine the overall risk level of the portfolio.
        
        Args:
            metrics: Dictionary of risk metrics
            alerts: List of risk alerts
            
        Returns:
            Risk level (low, medium, high, extreme)
        """
        # Count the number and severity of alerts
        num_alerts = len(alerts)
        
        # Check for specific high-risk metrics
        var = metrics.get('var', 0)
        var_threshold = self.risk_settings.get('var', {}).get('threshold', 0.05)
        
        exposure = metrics.get('exposure', 0)
        max_exposure = self.risk_settings.get('max_exposure_percent', {}).get('total', 80)
        
        volatility = metrics.get('volatility', 0)
        vol_threshold = self.risk_settings.get('market_risk', {}).get('volatility_threshold', 0.3)
        
        # Determine risk level based on metrics and alerts
        if var > var_threshold * 2 or exposure > max_exposure * 1.2 or num_alerts >= 3:
            return "extreme"
        elif var > var_threshold * 1.5 or exposure > max_exposure * 1.1 or num_alerts >= 2:
            return "high"
        elif var > var_threshold or exposure > max_exposure * 0.8 or num_alerts >= 1:
            return "medium"
        else:
            return "low"
    
    async def _trigger_emergency_protocols(self):
        """
        Trigger emergency protocols for extreme risk situations.
        
        This might include:
        - Automatically reducing high-risk positions
        - Setting up stop-loss orders
        - Notifying administrators
        """
        self.logger.warning("EMERGENCY PROTOCOL: Extreme risk detected!")
        
        # In a real implementation, this would execute risk reduction trades
        # For this prototype, we'll just log the emergency and simulate actions
        
        # Find the highest exposure assets
        high_exposure_assets = []
        for asset, data in self.portfolio['assets'].items():
            exposure = (data['value_usd'] / self.portfolio['total_value_usd']) * 100
            if exposure > 20:  # Assets with >20% exposure
                high_exposure_assets.append((asset, exposure, data['quantity']))
        
        # Sort by exposure (highest first)
        high_exposure_assets.sort(key=lambda x: x[1], reverse=True)
        
        # Simulate emergency actions
        for asset, exposure, quantity in high_exposure_assets:
            self.logger.warning(f"Emergency action: Reduce {asset} position (current exposure: {exposure:.2f}%)")
            
            # In a real implementation, this would send a trade execution request
            # For simulation, we'll just log it
            # 
            # Example code for real implementation:
            # if 'trade_execution_agent' in self.config.get('a2a', {}):
            #     trade_agent_url = self.config['a2a']['trade_execution_agent']
            #     try:
            #         trade_agent = self.a2a_client.discover_agent(trade_agent_url)
            #         self.a2a_client.create_task(
            #             agent_name=trade_agent['name'],
            #             capability='execute_trade',
            #             parameters={
            #                 'exchange': 'binance',
            #                 'crypto_pair': f"{asset}/USD",
            #                 'action': 'sell',
            #                 'order_type': 'market',
            #                 'quantity': quantity * 0.5  # Sell half the position
            #             }
            #         )
            #     except Exception as e:
            #         self.logger.error(f"Failed to execute emergency trade: {e}")
    
    async def start(self, host: str = "0.0.0.0", port: int = 8003):
        """
        Start the Risk Management Agent server.
        
        Args:
            host: Host to bind the server to
            port: Port to bind the server to
        """
        app = self.a2a_server.app
        
        # Add root endpoint for health checks
        @app.get("/")
        async def root():
            return {"status": "ok", "agent": self.name, "version": self.version}
        
        self.logger.info(f"Starting Risk Management Agent server on {host}:{port}")
        
        # Configure and start the server
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