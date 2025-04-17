"""
Integration Tests for Crypto Order Workflow with Agents

This module tests the integration between the crypto order workflow and the various agents in the system.
"""
import unittest
from unittest.mock import patch, MagicMock
import json
import requests
import uuid
from datetime import datetime

from src.workflows.crypto_order_workflow import (
    get_workflow,
    simulate_step_execution,
    CryptoOrderWorkflow
)


class MockResponse:
    """Mock response class for simulating requests"""
    
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
        self.content = json.dumps(json_data).encode('utf-8')
    
    def json(self):
        return self.json_data


class TestCryptoOrderAgentIntegration(unittest.TestCase):
    """Tests for integrating crypto order workflow with system agents"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_parameters = {
            "asset": "BTC",
            "order_type": "MARKET",
            "side": "BUY",
            "amount": 1000,
            "is_amount_in_usd": True,
            "portfolio_id": "test-portfolio"
        }
        
        # Agent information based on system status
        self.agent_info = {
            "market_analysis_agent": {
                "url": "http://market-analysis-agent:8001",
                "capabilities": ["market_analysis", "risk_assessment"]
            },
            "trade_execution_agent": {
                "url": "http://trade-execution-agent:8002",
                "capabilities": ["execute_trade", "get_order_status"]
            },
            "risk_management_agent": {
                "url": "http://risk-management-agent:8003",
                "capabilities": ["assess_trade_risk", "monitor_portfolio_risk"]
            },
            "reporting_analytics_agent": {
                "url": "http://reporting-analytics-agent:8004",
                "capabilities": ["generate_performance_report", "generate_portfolio_valuation"]
            }
        }
    
    @patch('requests.post')
    def test_market_analysis_agent_integration(self, mock_post):
        """Test integration with market analysis agent for risk assessment"""
        # Mock response data
        mock_data = {
            "status": "success",
            "risk_assessment": {
                "asset": "BTC",
                "volatility_risk": "medium",
                "market_sentiment": "positive",
                "correlation_risk": "low",
                "liquidity_risk": "low",
                "overall_risk_score": 0.42,
                "recommendation": "PROCEED",
                "timestamp": datetime.now().isoformat()
            }
        }
        mock_post.return_value = MockResponse(mock_data)
        
        # Create workflow
        workflow = CryptoOrderWorkflow(parameters=self.valid_parameters)
        
        # Simulate calling the market analysis agent
        response = self._call_agent_endpoint(
            self.agent_info["market_analysis_agent"]["url"],
            "/api/risk_assessment",
            {"asset": "BTC", "amount": 1000, "side": "BUY"}
        )
        
        # Verify response
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["risk_assessment"]["asset"], "BTC")
        self.assertEqual(response["risk_assessment"]["recommendation"], "PROCEED")
        
        # Verify mock was called with correct data
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], f"{self.agent_info['market_analysis_agent']['url']}/api/risk_assessment")
        
        # Verify payload content
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(payload["asset"], "BTC")
        self.assertEqual(payload["amount"], 1000)
        self.assertEqual(payload["side"], "BUY")
    
    @patch('requests.post')
    def test_trade_execution_agent_integration(self, mock_post):
        """Test integration with trade execution agent for order execution"""
        # Mock response data
        order_id = f"ord_{uuid.uuid4().hex[:12]}"
        mock_data = {
            "status": "success",
            "order": {
                "order_id": order_id,
                "exchange": "binance",
                "asset": "BTC",
                "order_type": "MARKET",
                "side": "BUY",
                "amount_crypto": 0.017113,
                "price": 58432.15,
                "status": "FILLED",
                "filled_amount": 0.017113,
                "remaining_amount": 0.0,
                "timestamp": datetime.now().isoformat()
            }
        }
        mock_post.return_value = MockResponse(mock_data)
        
        # Simulate calling the trade execution agent
        response = self._call_agent_endpoint(
            self.agent_info["trade_execution_agent"]["url"],
            "/api/execute_trade",
            {
                "asset": "BTC",
                "order_type": "MARKET",
                "side": "BUY",
                "amount": 0.017113,
                "is_amount_in_crypto": True
            }
        )
        
        # Verify response
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["order"]["asset"], "BTC")
        self.assertEqual(response["order"]["order_type"], "MARKET")
        self.assertEqual(response["order"]["status"], "FILLED")
        
        # Verify mock was called with correct data
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], f"{self.agent_info['trade_execution_agent']['url']}/api/execute_trade")
    
    @patch('requests.get')
    def test_trade_execution_agent_order_status(self, mock_get):
        """Test integration with trade execution agent for order status"""
        # Mock response data
        order_id = f"ord_{uuid.uuid4().hex[:12]}"
        mock_data = {
            "status": "success",
            "order": {
                "order_id": order_id,
                "exchange": "binance",
                "asset": "BTC",
                "order_type": "MARKET",
                "side": "BUY",
                "price": 58432.15,
                "status": "FILLED",
                "filled_amount": 0.017113,
                "remaining_amount": 0.0,
                "timestamp": datetime.now().isoformat(),
                "transaction_ids": [f"tx_{uuid.uuid4().hex[:8]}" for _ in range(3)]
            }
        }
        mock_get.return_value = MockResponse(mock_data)
        
        # Simulate getting order status
        response = self._call_agent_endpoint(
            self.agent_info["trade_execution_agent"]["url"],
            f"/api/orders/{order_id}",
            method="GET"
        )
        
        # Verify response
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["order"]["order_id"], order_id)
        self.assertEqual(response["order"]["status"], "FILLED")
        
        # Verify mock was called with correct URL
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args[0][0], f"{self.agent_info['trade_execution_agent']['url']}/api/orders/{order_id}")
    
    @patch('requests.post')
    def test_risk_management_agent_integration(self, mock_post):
        """Test integration with risk management agent for trade risk assessment"""
        # Mock response data
        mock_data = {
            "status": "success",
            "trade_risk": {
                "asset": "BTC",
                "side": "BUY",
                "amount_usd": 1000,
                "portfolio_impact": 0.032,  # 3.2% of portfolio
                "position_concentration_after": 0.423,  # 42.3% in BTC after trade
                "risk_level": "MEDIUM",
                "within_risk_limits": True,
                "warnings": [
                    "Position concentration exceeds recommended 40% threshold"
                ],
                "timestamp": datetime.now().isoformat()
            }
        }
        mock_post.return_value = MockResponse(mock_data)
        
        # Simulate calling the risk management agent
        response = self._call_agent_endpoint(
            self.agent_info["risk_management_agent"]["url"],
            "/api/assess_trade_risk",
            {
                "asset": "BTC",
                "side": "BUY",
                "amount_usd": 1000,
                "portfolio_id": "test-portfolio"
            }
        )
        
        # Verify response
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["trade_risk"]["asset"], "BTC")
        self.assertEqual(response["trade_risk"]["risk_level"], "MEDIUM")
        self.assertTrue(response["trade_risk"]["within_risk_limits"])
        
        # Verify mock was called with correct data
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], f"{self.agent_info['risk_management_agent']['url']}/api/assess_trade_risk")
        
        # Verify payload content
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(payload["asset"], "BTC")
        self.assertEqual(payload["amount_usd"], 1000)
    
    @patch('requests.post')
    def test_reporting_agent_portfolio_update(self, mock_post):
        """Test integration with reporting agent for portfolio updates"""
        # Mock response data
        mock_data = {
            "status": "success",
            "portfolio_update": {
                "portfolio_id": "test-portfolio",
                "timestamp": datetime.now().isoformat(),
                "successful": True,
                "new_balance": {
                    "BTC": 0.517113,  # Previous 0.5 + new 0.017113
                    "ETH": 5.0,
                    "SOL": 50.0,
                    "USD": 25000.50 - 1000  # $1000 spent on BTC
                },
                "total_value_usd": 29540.35,
                "allocation": {
                    "BTC": 0.704,  # 70.4%
                    "ETH": 0.144,  # 14.4%
                    "SOL": 0.113,  # 11.3%
                    "USD": 0.039   # 3.9%
                }
            }
        }
        mock_post.return_value = MockResponse(mock_data)
        
        # Simulate calling the reporting agent
        response = self._call_agent_endpoint(
            self.agent_info["reporting_analytics_agent"]["url"],
            "/api/generate_portfolio_valuation",
            {
                "portfolio_id": "test-portfolio",
                "include_allocation": True,
                "include_history": False
            }
        )
        
        # Verify response
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["portfolio_update"]["portfolio_id"], "test-portfolio")
        self.assertTrue(response["portfolio_update"]["successful"])
        
        # Check portfolio values
        self.assertEqual(response["portfolio_update"]["new_balance"]["BTC"], 0.517113)
        self.assertAlmostEqual(response["portfolio_update"]["allocation"]["BTC"], 0.704, places=3)
        
        # Verify mock was called with correct data
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], f"{self.agent_info['reporting_analytics_agent']['url']}/api/generate_portfolio_valuation")
    
    @patch('requests.post')
    def test_workflow_with_market_analysis_risk_check(self, mock_post):
        """Test workflow step that performs risk assessment via market analysis agent"""
        # Mock response data
        mock_data = {
            "status": "success",
            "risk_assessment": {
                "asset": "BTC",
                "volatility_risk": "medium",
                "market_sentiment": "positive",
                "overall_risk_score": 0.42,
                "recommendation": "PROCEED"
            }
        }
        mock_post.return_value = MockResponse(mock_data)
        
        # Create workflow and add a custom risk assessment step
        workflow = CryptoOrderWorkflow(parameters=self.valid_parameters)
        
        # Simulate a risk assessment step
        # In a real implementation, this would be part of the workflow steps
        result = self._call_risk_assessment_step(workflow.parameters)
        
        # Verify result
        self.assertEqual(result["assessment"]["asset"], "BTC")
        self.assertEqual(result["assessment"]["recommendation"], "PROCEED")
        self.assertTrue(result["proceed_with_order"])
        
        # Verify mock was called
        mock_post.assert_called_once()
    
    def test_complete_order_workflow_simulation(self):
        """Test a complete order workflow with all required steps"""
        # This test would mock all agent calls in a workflow execution
        # Create the workflow
        workflow = get_workflow(self.valid_parameters)
        
        # Mock execution context for the workflow
        context = {}
        
        # Step 1: Validate order parameters
        step_result = simulate_step_execution("validate_order_params", workflow.parameters, context)
        context["validate_order_params"] = step_result
        self.assertTrue(step_result["validation_result"]["valid"])
        
        # Step 2: Check available funds
        step_result = simulate_step_execution("check_available_funds", workflow.parameters, context)
        context["check_available_funds"] = step_result
        self.assertTrue(step_result["funds_check"]["sufficient_funds"])
        
        # Step 3: Calculate order details
        step_result = simulate_step_execution("calculate_order_details", workflow.parameters, context)
        context["calculate_order_details"] = step_result
        self.assertGreater(step_result["order_details"]["amount_crypto"], 0)
        
        # Step 4: Submit order
        step_result = simulate_step_execution("submit_order", workflow.parameters, context)
        context["submit_order"] = step_result
        self.assertTrue(step_result["order_submission"]["success"])
        
        # Step 5: Monitor order status
        step_result = simulate_step_execution("monitor_order_status", workflow.parameters, context)
        context["monitor_order_status"] = step_result
        self.assertEqual(step_result["order_status"]["status"], "FILLED")
        
        # Step 6: Update portfolio
        step_result = simulate_step_execution("update_portfolio", workflow.parameters, context)
        context["update_portfolio"] = step_result
        self.assertTrue(step_result["portfolio_update"]["successful"])
        
        # Verify the complete workflow execution
        self.assertEqual(len(context), 6)  # All 6 steps executed
    
    def _call_agent_endpoint(self, base_url, endpoint, data=None, method="POST"):
        """Helper method to call an agent endpoint"""
        url = f"{base_url}{endpoint}"
        
        if method == "POST":
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, data=json.dumps(data), headers=headers)
        else:  # GET
            response = requests.get(url)
        
        return response.json()
    
    def _call_risk_assessment_step(self, params):
        """Simulate a risk assessment step using market analysis agent"""
        asset = params["asset"]
        amount = params["amount"]
        side = params["side"]
        
        # Call the agent endpoint
        response = self._call_agent_endpoint(
            self.agent_info["market_analysis_agent"]["url"],
            "/api/risk_assessment",
            {"asset": asset, "amount": amount, "side": side}
        )
        
        # Process the response
        proceed = (
            response["status"] == "success" and 
            response["risk_assessment"]["recommendation"] == "PROCEED"
        )
        
        return {
            "assessment": response["risk_assessment"],
            "proceed_with_order": proceed,
            "timestamp": datetime.now().isoformat()
        }


if __name__ == '__main__':
    unittest.main() 