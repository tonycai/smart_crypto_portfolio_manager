"""
Market Analysis Agent for Smart Crypto Portfolio Manager

This agent monitors crypto markets, analyzes trends, and identifies trading opportunities.
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

import uvicorn
import pandas as pd
import numpy as np
from fastapi import FastAPI

# Import the A2A server implementation
import sys
# Use relative import path instead of hardcoded path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from a2a.server import create_a2a_server
from a2a.client import A2AClient


class MarketAnalysisAgent:
    """
    Agent for analyzing cryptocurrency markets and identifying trading opportunities.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the Market Analysis Agent.
        
        Args:
            config_path: Path to the configuration file (optional)
        """
        self.name = "Market Analysis Agent"
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
        self.a2a_server.register_capability_handler('market_analysis', self.analyze_market)
        self.a2a_server.register_capability_handler('risk_assessment', self.assess_risk)
        
        # Initialize market data storage
        self.market_data = {}
    
    async def analyze_market(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market data for a specific cryptocurrency pair.
        
        Args:
            parameters: Parameters for the analysis
            
        Returns:
            Analysis results
        """
        self.logger.info(f"Analyzing market for {parameters}")
        
        # Extract parameters
        crypto_pair = parameters.get('crypto_pair')
        timeframe = parameters.get('timeframe', '1d')
        indicators = parameters.get('indicators', ['rsi', 'macd', 'bollinger'])
        
        if not crypto_pair:
            raise ValueError("crypto_pair parameter is required")
        
        # In a real implementation, this would fetch data from exchanges
        # For this prototype, we'll simulate some market data
        market_data = self._simulate_market_data(crypto_pair, timeframe)
        
        # Calculate technical indicators
        analysis_result = self._calculate_indicators(market_data, indicators)
        
        # Determine the overall trend
        trend, confidence = self._determine_trend(analysis_result)
        
        # Generate trading signals
        signals = self._generate_signals(market_data, analysis_result, trend)
        
        return {
            "trend": trend,
            "confidence": confidence,
            "signals": signals,
            "analysis": analysis_result
        }
    
    async def assess_risk(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform initial risk assessment for a potential trade.
        
        Args:
            parameters: Parameters for the risk assessment
            
        Returns:
            Risk assessment results
        """
        self.logger.info(f"Assessing risk for {parameters}")
        
        # Extract parameters
        crypto_pair = parameters.get('crypto_pair')
        position_size = parameters.get('position_size')
        entry_price = parameters.get('entry_price')
        
        if not crypto_pair or position_size is None:
            raise ValueError("crypto_pair and position_size parameters are required")
        
        # In a real implementation, this would analyze risk factors
        # For this prototype, we'll simulate a simple risk assessment
        
        # Simulate volatility (higher means more risk)
        volatility = self._simulate_volatility(crypto_pair)
        
        # Calculate risk level based on volatility and position size
        risk_level, recommendation = self._calculate_risk_level(volatility, position_size)
        
        return {
            "risk_level": risk_level,
            "recommendation": recommendation,
            "volatility": volatility,
            "max_recommended_size": position_size * (0.5 / volatility) if volatility > 0.5 else position_size
        }
    
    def _simulate_market_data(self, crypto_pair: str, timeframe: str) -> pd.DataFrame:
        """
        Simulate market data for testing purposes.
        
        Args:
            crypto_pair: The cryptocurrency trading pair
            timeframe: The timeframe for the data
            
        Returns:
            DataFrame with simulated market data
        """
        # Generate dates
        periods = 100
        end_date = datetime.now()
        date_range = pd.date_range(end=end_date, periods=periods, freq='D')
        
        # Generate price data with some randomness
        seed = hash(crypto_pair) % 10000
        np.random.seed(seed)
        
        # Start with a base price between 100 and 50000
        base_price = np.random.uniform(100, 50000)
        
        # Generate price movements with trends and volatility
        price_changes = np.random.normal(0, 0.02, periods)
        price_changes = price_changes.cumsum()
        
        # Add a trend based on crypto_pair
        if 'BTC' in crypto_pair:
            price_changes += np.linspace(0, 0.1, periods)  # Slight uptrend for BTC
        elif 'ETH' in crypto_pair:
            price_changes += np.linspace(0, 0.15, periods)  # Stronger uptrend for ETH
        
        # Calculate prices
        prices = base_price * (1 + price_changes)
        
        # Generate volume
        volumes = base_price * np.random.uniform(0.5, 5, periods) * 10
        
        # Create DataFrame
        data = pd.DataFrame({
            'date': date_range,
            'open': prices * np.random.uniform(0.99, 1.01, periods),
            'high': prices * np.random.uniform(1.01, 1.03, periods),
            'low': prices * np.random.uniform(0.97, 0.99, periods),
            'close': prices,
            'volume': volumes
        })
        
        return data
    
    def _calculate_indicators(self, data: pd.DataFrame, indicators: List[str]) -> Dict[str, Any]:
        """
        Calculate technical indicators for the market data.
        
        Args:
            data: DataFrame with market data
            indicators: List of indicators to calculate
            
        Returns:
            Dictionary with calculated indicators
        """
        result = {}
        
        # Calculate RSI
        if 'rsi' in indicators:
            delta = data['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            result['rsi'] = rsi.iloc[-1]
            result['rsi_values'] = rsi.dropna().tolist()
        
        # Calculate MACD
        if 'macd' in indicators:
            ema12 = data['close'].ewm(span=12).mean()
            ema26 = data['close'].ewm(span=26).mean()
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9).mean()
            histogram = macd_line - signal_line
            
            result['macd'] = {
                'macd_line': macd_line.iloc[-1],
                'signal_line': signal_line.iloc[-1],
                'histogram': histogram.iloc[-1],
                'macd_values': macd_line.dropna().tolist(),
                'signal_values': signal_line.dropna().tolist(),
                'histogram_values': histogram.dropna().tolist()
            }
        
        # Calculate Bollinger Bands
        if 'bollinger' in indicators:
            window = 20
            sma = data['close'].rolling(window=window).mean()
            std = data['close'].rolling(window=window).std()
            upper_band = sma + (std * 2)
            lower_band = sma - (std * 2)
            
            result['bollinger'] = {
                'sma': sma.iloc[-1],
                'upper_band': upper_band.iloc[-1],
                'lower_band': lower_band.iloc[-1],
                'current_price': data['close'].iloc[-1],
                'percent_b': (data['close'].iloc[-1] - lower_band.iloc[-1]) / (upper_band.iloc[-1] - lower_band.iloc[-1])
            }
        
        return result
    
    def _determine_trend(self, analysis: Dict[str, Any]) -> tuple:
        """
        Determine the overall market trend based on indicators.
        
        Args:
            analysis: Dictionary with calculated indicators
            
        Returns:
            Tuple of (trend, confidence)
        """
        signals = []
        
        # Check RSI
        if 'rsi' in analysis:
            rsi = analysis['rsi']
            if rsi > 70:
                signals.append(('bearish', 0.7))
            elif rsi < 30:
                signals.append(('bullish', 0.7))
            elif rsi > 60:
                signals.append(('bullish', 0.3))
            elif rsi < 40:
                signals.append(('bearish', 0.3))
            else:
                signals.append(('neutral', 0.5))
        
        # Check MACD
        if 'macd' in analysis:
            macd = analysis['macd']
            if macd['macd_line'] > macd['signal_line'] and macd['histogram'] > 0:
                signals.append(('bullish', 0.6))
            elif macd['macd_line'] < macd['signal_line'] and macd['histogram'] < 0:
                signals.append(('bearish', 0.6))
            else:
                signals.append(('neutral', 0.4))
        
        # Check Bollinger Bands
        if 'bollinger' in analysis:
            bollinger = analysis['bollinger']
            percent_b = bollinger['percent_b']
            
            if percent_b > 1:
                signals.append(('bearish', 0.8))  # Price above upper band
            elif percent_b < 0:
                signals.append(('bullish', 0.8))  # Price below lower band
            elif percent_b > 0.8:
                signals.append(('bearish', 0.4))  # Near upper band
            elif percent_b < 0.2:
                signals.append(('bullish', 0.4))  # Near lower band
            else:
                signals.append(('neutral', 0.5))  # In the middle
        
        # Calculate overall trend and confidence
        if not signals:
            return 'neutral', 0.5
        
        # Count votes for each trend
        trend_votes = {'bullish': 0, 'neutral': 0, 'bearish': 0}
        total_confidence = 0
        
        for trend, confidence in signals:
            trend_votes[trend] += confidence
            total_confidence += confidence
        
        # Determine the winning trend
        if trend_votes['bullish'] > trend_votes['bearish'] and trend_votes['bullish'] > trend_votes['neutral']:
            return 'bullish', trend_votes['bullish'] / total_confidence
        elif trend_votes['bearish'] > trend_votes['bullish'] and trend_votes['bearish'] > trend_votes['neutral']:
            return 'bearish', trend_votes['bearish'] / total_confidence
        else:
            return 'neutral', trend_votes['neutral'] / total_confidence
    
    def _generate_signals(
        self, 
        data: pd.DataFrame, 
        analysis: Dict[str, Any], 
        trend: str
    ) -> List[Dict[str, Any]]:
        """
        Generate trading signals based on analysis.
        
        Args:
            data: DataFrame with market data
            analysis: Dictionary with calculated indicators
            trend: Overall trend ('bullish', 'bearish', 'neutral')
            
        Returns:
            List of trading signals
        """
        signals = []
        
        # Current price
        current_price = data['close'].iloc[-1]
        
        # RSI-based signals
        if 'rsi' in analysis:
            rsi = analysis['rsi']
            if rsi < 30 and trend == 'bullish':
                signals.append({
                    'type': 'buy',
                    'reason': 'RSI oversold',
                    'strength': 'strong',
                    'metric': 'rsi',
                    'value': rsi
                })
            elif rsi > 70 and trend == 'bearish':
                signals.append({
                    'type': 'sell',
                    'reason': 'RSI overbought',
                    'strength': 'strong',
                    'metric': 'rsi',
                    'value': rsi
                })
        
        # MACD-based signals
        if 'macd' in analysis:
            macd = analysis['macd']
            
            # MACD line crosses above signal line (bullish crossover)
            if len(analysis['macd'].get('macd_values', [])) > 2 and len(analysis['macd'].get('signal_values', [])) > 2:
                macd_values = analysis['macd']['macd_values']
                signal_values = analysis['macd']['signal_values']
                
                # Check for crossover (macd line was below signal line and is now above)
                if macd_values[-2] < signal_values[-2] and macd_values[-1] > signal_values[-1]:
                    signals.append({
                        'type': 'buy',
                        'reason': 'MACD bullish crossover',
                        'strength': 'medium',
                        'metric': 'macd',
                        'value': {
                            'macd': macd['macd_line'],
                            'signal': macd['signal_line']
                        }
                    })
                # Check for bearish crossover
                elif macd_values[-2] > signal_values[-2] and macd_values[-1] < signal_values[-1]:
                    signals.append({
                        'type': 'sell',
                        'reason': 'MACD bearish crossover',
                        'strength': 'medium',
                        'metric': 'macd',
                        'value': {
                            'macd': macd['macd_line'],
                            'signal': macd['signal_line']
                        }
                    })
        
        # Bollinger Bands-based signals
        if 'bollinger' in analysis:
            bollinger = analysis['bollinger']
            
            # Price below lower band (potential buy)
            if current_price < bollinger['lower_band'] and trend != 'bearish':
                signals.append({
                    'type': 'buy',
                    'reason': 'Price below Bollinger lower band',
                    'strength': 'medium',
                    'metric': 'bollinger',
                    'value': {
                        'price': current_price,
                        'lower_band': bollinger['lower_band']
                    }
                })
            
            # Price above upper band (potential sell)
            elif current_price > bollinger['upper_band'] and trend != 'bullish':
                signals.append({
                    'type': 'sell',
                    'reason': 'Price above Bollinger upper band',
                    'strength': 'medium',
                    'metric': 'bollinger',
                    'value': {
                        'price': current_price,
                        'upper_band': bollinger['upper_band']
                    }
                })
        
        return signals
    
    def _simulate_volatility(self, crypto_pair: str) -> float:
        """
        Simulate volatility for a cryptocurrency pair.
        
        Args:
            crypto_pair: The cryptocurrency trading pair
            
        Returns:
            Volatility as a float between 0 and 1
        """
        # Seed based on crypto pair for consistent results
        seed = hash(crypto_pair) % 10000
        np.random.seed(seed)
        
        # Base volatility
        base_volatility = np.random.uniform(0.2, 0.8)
        
        # Adjust based on well-known cryptocurrencies
        if 'BTC' in crypto_pair:
            base_volatility *= 0.8  # BTC is relatively less volatile
        elif 'ETH' in crypto_pair:
            base_volatility *= 0.9
        elif any(x in crypto_pair for x in ['DOGE', 'SHIB', 'SAFEMOON']):
            base_volatility *= 1.5  # Meme coins are more volatile
        
        return min(base_volatility, 1.0)  # Ensure it's between 0 and 1
    
    def _calculate_risk_level(self, volatility: float, position_size: float) -> tuple:
        """
        Calculate risk level based on volatility and position size.
        
        Args:
            volatility: Volatility of the cryptocurrency (0-1)
            position_size: Size of the position to take
            
        Returns:
            Tuple of (risk_level, recommendation)
        """
        # Risk level thresholds
        LOW_RISK = 0.3
        MEDIUM_RISK = 0.6
        HIGH_RISK = 0.8
        
        # Adjust for position size (bigger positions are riskier)
        # In a real system, this would be relative to portfolio size and risk tolerance
        position_factor = min(position_size / 1000, 1.0)  # Simplified scaling
        
        # Calculate combined risk
        combined_risk = volatility * (0.7 + 0.3 * position_factor)
        
        # Determine risk level
        if combined_risk < LOW_RISK:
            return 'low', 'Proceed with the trade'
        elif combined_risk < MEDIUM_RISK:
            return 'medium', 'Proceed with caution'
        elif combined_risk < HIGH_RISK:
            return 'high', 'Consider reducing position size'
        else:
            return 'extreme', 'Not recommended, high risk of loss'
    
    async def monitor_markets(self, crypto_pairs: List[str], interval_seconds: int = 60):
        """
        Continuously monitor markets for trading opportunities.
        
        Args:
            crypto_pairs: List of cryptocurrency pairs to monitor
            interval_seconds: Interval between scans in seconds
        """
        self.logger.info(f"Starting market monitoring for {crypto_pairs}")
        
        while True:
            try:
                for crypto_pair in crypto_pairs:
                    # Analyze the market
                    analysis_result = await self.analyze_market({
                        'crypto_pair': crypto_pair,
                        'timeframe': '1h',
                        'indicators': ['rsi', 'macd', 'bollinger']
                    })
                    
                    # Check if there are any strong signals
                    strong_signals = [s for s in analysis_result.get('signals', []) 
                                    if s.get('strength') == 'strong']
                    
                    if strong_signals:
                        self.logger.info(f"Strong signals detected for {crypto_pair}: {strong_signals}")
                        
                        # In a real implementation, we would notify the Trade Execution Agent
                        # For example:
                        # for signal in strong_signals:
                        #     if signal['type'] == 'buy':
                        #         await self._notify_trade_execution_agent(crypto_pair, 'buy', ...)
                    
                self.logger.debug(f"Market monitoring cycle completed for {crypto_pairs}")
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                self.logger.error(f"Error in market monitoring: {e}")
                await asyncio.sleep(interval_seconds)
    
    async def start(self, host: str = "0.0.0.0", port: int = 8001):
        """
        Start the Market Analysis Agent server.
        
        Args:
            host: Host to bind the server to
            port: Port to bind the server to
        """
        self.logger.info(f"Starting Market Analysis Agent server on {host}:{port}")
        
        # Start the FastAPI server
        config = uvicorn.Config(self.a2a_server.app, host=host, port=port)
        server = uvicorn.Server(config)
        
        # Start the market monitoring in the background
        crypto_pairs_to_monitor = self.config.get('crypto_pairs_to_monitor', ['BTC/USD', 'ETH/USD'])
        monitoring_task = asyncio.create_task(self.monitor_markets(crypto_pairs_to_monitor))
        
        # Run the server
        await server.serve()
        
        # Cancel the monitoring task when the server stops
        monitoring_task.cancel()


async def main():
    """Main entry point for the Market Analysis Agent."""
    # Initialize the agent
    agent = MarketAnalysisAgent()
    
    # Start the agent server
    await agent.start()


if __name__ == "__main__":
    asyncio.run(main())
