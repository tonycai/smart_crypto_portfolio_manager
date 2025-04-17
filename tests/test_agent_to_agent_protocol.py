"""
Unit Tests for Agent-to-Agent (A2A) Protocol

This module tests the communication protocol between different agents in the system,
ensuring they can exchange messages in a standardized format and process responses correctly.
"""
import unittest
from unittest.mock import patch, MagicMock
import json
import uuid
import requests
from datetime import datetime

class MockResponse:
    """Mock response class for simulating HTTP requests"""
    
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
        self.content = json.dumps(json_data).encode('utf-8')
    
    def json(self):
        return self.json_data


class TestAgentToAgentProtocol(unittest.TestCase):
    """Tests for agent-to-agent communication protocol"""
    
    def setUp(self):
        """Set up test data and mocks"""
        self.agent_endpoints = {
            "market_analysis_agent": "http://market-analysis-agent:8001",
            "trade_execution_agent": "http://trade-execution-agent:8002",
            "risk_management_agent": "http://risk-management-agent:8003",
            "portfolio_agent": "http://portfolio-agent:8004",
            "reporting_agent": "http://reporting-agent:8005",
        }
        
        # Standard A2A message format
        self.base_message = {
            "message_id": str(uuid.uuid4()),
            "sender": "orchestration_agent",
            "timestamp": datetime.utcnow().isoformat(),
            "request_type": "",
            "payload": {}
        }
    
    @patch('requests.post')
    def test_a2a_basic_message_structure(self, mock_post):
        """Test the structure of agent-to-agent messages"""
        # Configure mock response
        mock_response = {
            "message_id": str(uuid.uuid4()),
            "reference_id": "",
            "sender": "trade_execution_agent",
            "receiver": "orchestration_agent",
            "timestamp": datetime.utcnow().isoformat(),
            "response_type": "execute_trade_response",
            "status": "success",
            "payload": {
                "order_id": f"ord_{uuid.uuid4().hex[:12]}",
                "status": "FILLED"
            }
        }
        mock_post.return_value = MockResponse(mock_response)
        
        # Create a message to send
        message = self.base_message.copy()
        message.update({
            "receiver": "trade_execution_agent",
            "request_type": "execute_trade_request",
            "payload": {
                "asset": "BTC",
                "order_type": "MARKET",
                "side": "BUY",
                "amount": 0.5,
                "is_amount_in_crypto": True
            }
        })
        
        # Reference the message being sent
        message_id = message["message_id"]
        
        # Call the trade execution agent
        response = self.send_a2a_message(
            self.agent_endpoints["trade_execution_agent"],
            message
        )
        
        # Verify the message structure (both sent and received)
        self.assertIn("message_id", message)
        self.assertIn("sender", message)
        self.assertIn("receiver", message)
        self.assertIn("timestamp", message)
        self.assertIn("request_type", message)
        self.assertIn("payload", message)
        
        # Verify response structure
        self.assertIn("message_id", response)
        self.assertIn("reference_id", response)
        self.assertIn("sender", response)
        self.assertIn("receiver", response)
        self.assertIn("timestamp", response)
        self.assertIn("response_type", response)
        self.assertIn("status", response)
        self.assertIn("payload", response)
        
        # Verify reference_id matches our message_id
        self.assertEqual(response["reference_id"], message_id)
        
        # Verify sender/receiver are correct
        self.assertEqual(response["sender"], "trade_execution_agent")
        self.assertEqual(response["receiver"], "orchestration_agent")
        
        # Verify request/response types match
        self.assertEqual(message["request_type"], "execute_trade_request")
        self.assertEqual(response["response_type"], "execute_trade_response")
    
    @patch('requests.post')
    def test_a2a_market_analysis_request(self, mock_post):
        """Test market analysis agent protocol for risk assessment"""
        # Configure mock response
        mock_response = {
            "message_id": str(uuid.uuid4()),
            "reference_id": "",
            "sender": "market_analysis_agent",
            "receiver": "orchestration_agent",
            "timestamp": datetime.utcnow().isoformat(),
            "response_type": "risk_assessment_response",
            "status": "success",
            "payload": {
                "asset": "BTC",
                "volatility_risk": "medium",
                "market_sentiment": "positive",
                "correlation_risk": "low",
                "liquidity_risk": "low",
                "overall_risk_score": 0.42,
                "recommendation": "PROCEED"
            }
        }
        mock_post.return_value = MockResponse(mock_response)
        
        # Create a risk assessment request
        message = self.base_message.copy()
        message.update({
            "receiver": "market_analysis_agent",
            "request_type": "risk_assessment_request",
            "payload": {
                "asset": "BTC",
                "amount": 1000,
                "side": "BUY",
                "time_horizon": "short_term"
            }
        })
        
        # Send the message
        response = self.send_a2a_message(
            self.agent_endpoints["market_analysis_agent"],
            message
        )
        
        # Verify the response
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["response_type"], "risk_assessment_response")
        self.assertEqual(response["payload"]["asset"], "BTC")
        self.assertEqual(response["payload"]["recommendation"], "PROCEED")
    
    @patch('requests.post')
    def test_a2a_trade_execution_request(self, mock_post):
        """Test trade execution agent protocol for executing trades"""
        # Configure mock response
        order_id = f"ord_{uuid.uuid4().hex[:12]}"
        mock_response = {
            "message_id": str(uuid.uuid4()),
            "reference_id": "",
            "sender": "trade_execution_agent",
            "receiver": "orchestration_agent",
            "timestamp": datetime.utcnow().isoformat(),
            "response_type": "execute_trade_response",
            "status": "success",
            "payload": {
                "order_id": order_id,
                "exchange": "binance",
                "asset": "BTC",
                "order_type": "MARKET",
                "side": "BUY",
                "amount_crypto": 0.5,
                "price": 58432.15,
                "status": "FILLED",
                "filled_amount": 0.5,
                "remaining_amount": 0.0,
            }
        }
        mock_post.return_value = MockResponse(mock_response)
        
        # Create a trade execution request
        message = self.base_message.copy()
        message.update({
            "receiver": "trade_execution_agent",
            "request_type": "execute_trade_request",
            "payload": {
                "asset": "BTC",
                "order_type": "MARKET",
                "side": "BUY",
                "amount": 0.5,
                "is_amount_in_crypto": True,
                "exchange": "binance"
            }
        })
        
        # Send the message
        response = self.send_a2a_message(
            self.agent_endpoints["trade_execution_agent"],
            message
        )
        
        # Verify the response
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["response_type"], "execute_trade_response")
        self.assertEqual(response["payload"]["asset"], "BTC")
        self.assertEqual(response["payload"]["order_id"], order_id)
        self.assertEqual(response["payload"]["status"], "FILLED")
    
    @patch('requests.post')
    def test_a2a_portfolio_update_request(self, mock_post):
        """Test portfolio agent protocol for updating portfolio"""
        # Configure mock response
        mock_response = {
            "message_id": str(uuid.uuid4()),
            "reference_id": "",
            "sender": "portfolio_agent",
            "receiver": "orchestration_agent",
            "timestamp": datetime.utcnow().isoformat(),
            "response_type": "portfolio_update_response",
            "status": "success",
            "payload": {
                "portfolio_id": "default-portfolio",
                "transaction_id": str(uuid.uuid4()),
                "successful": True,
                "new_balances": {
                    "BTC": 2.5,
                    "USD": 45000.50
                },
                "changes": {
                    "BTC": 0.5,
                    "USD": -29216.08  # 0.5 BTC at $58,432.15
                }
            }
        }
        mock_post.return_value = MockResponse(mock_response)
        
        # Create a portfolio update request
        message = self.base_message.copy()
        message.update({
            "receiver": "portfolio_agent",
            "request_type": "portfolio_update_request",
            "payload": {
                "portfolio_id": "default-portfolio",
                "asset": "BTC",
                "transaction_type": "BUY",
                "amount": 0.5,
                "price": 58432.15,
                "timestamp": datetime.utcnow().isoformat(),
                "transaction_details": {
                    "order_id": f"ord_{uuid.uuid4().hex[:12]}",
                    "exchange": "binance",
                    "fee": 0.001
                }
            }
        })
        
        # Send the message
        response = self.send_a2a_message(
            self.agent_endpoints["portfolio_agent"],
            message
        )
        
        # Verify the response
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["response_type"], "portfolio_update_response")
        self.assertTrue(response["payload"]["successful"])
        self.assertIn("BTC", response["payload"]["new_balances"])
        self.assertIn("USD", response["payload"]["new_balances"])
    
    @patch('requests.post')
    def test_a2a_risk_assessment_request(self, mock_post):
        """Test risk management agent protocol for trade risk assessment"""
        # Configure mock response
        mock_response = {
            "message_id": str(uuid.uuid4()),
            "reference_id": "",
            "sender": "risk_management_agent",
            "receiver": "orchestration_agent",
            "timestamp": datetime.utcnow().isoformat(),
            "response_type": "trade_risk_assessment_response",
            "status": "success",
            "payload": {
                "asset": "BTC",
                "side": "BUY",
                "amount_usd": 29216.08,
                "portfolio_impact": 0.393,  # 39.3% of portfolio
                "position_concentration_after": 0.65,  # 65% in BTC after trade
                "risk_level": "HIGH",
                "within_risk_limits": False,
                "warnings": [
                    "Position concentration exceeds recommended 60% threshold",
                    "Single trade exceeds recommended 30% of portfolio threshold"
                ]
            }
        }
        mock_post.return_value = MockResponse(mock_response)
        
        # Create a risk assessment request
        message = self.base_message.copy()
        message.update({
            "receiver": "risk_management_agent",
            "request_type": "trade_risk_assessment_request",
            "payload": {
                "asset": "BTC",
                "side": "BUY",
                "amount_crypto": 0.5,
                "amount_usd": 29216.08,
                "portfolio_id": "default-portfolio"
            }
        })
        
        # Send the message
        response = self.send_a2a_message(
            self.agent_endpoints["risk_management_agent"],
            message
        )
        
        # Verify the response
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["response_type"], "trade_risk_assessment_response")
        self.assertEqual(response["payload"]["risk_level"], "HIGH")
        self.assertFalse(response["payload"]["within_risk_limits"])
        self.assertTrue(len(response["payload"]["warnings"]) > 0)
    
    @patch('requests.post')
    def test_a2a_request_chain(self, mock_post):
        """Test a chain of agent-to-agent requests for a workflow"""
        # We'll create a series of mock responses to simulate a workflow
        
        # 1. Risk assessment response
        risk_response = {
            "message_id": str(uuid.uuid4()),
            "reference_id": "",
            "sender": "market_analysis_agent",
            "receiver": "orchestration_agent",
            "timestamp": datetime.utcnow().isoformat(),
            "response_type": "risk_assessment_response",
            "status": "success",
            "payload": {
                "asset": "BTC",
                "recommendation": "PROCEED",
                "overall_risk_score": 0.42
            }
        }
        
        # 2. Portfolio check response
        portfolio_check_response = {
            "message_id": str(uuid.uuid4()),
            "reference_id": "",
            "sender": "portfolio_agent",
            "receiver": "orchestration_agent",
            "timestamp": datetime.utcnow().isoformat(),
            "response_type": "portfolio_check_response",
            "status": "success",
            "payload": {
                "portfolio_id": "default-portfolio",
                "sufficient_funds": True,
                "available_funds": {
                    "USD": 75000.0
                }
            }
        }
        
        # 3. Trade execution response
        order_id = f"ord_{uuid.uuid4().hex[:12]}"
        trade_response = {
            "message_id": str(uuid.uuid4()),
            "reference_id": "",
            "sender": "trade_execution_agent",
            "receiver": "orchestration_agent",
            "timestamp": datetime.utcnow().isoformat(),
            "response_type": "execute_trade_response",
            "status": "success",
            "payload": {
                "order_id": order_id,
                "asset": "BTC",
                "status": "FILLED",
                "price": 58432.15
            }
        }
        
        # 4. Portfolio update response
        portfolio_update_response = {
            "message_id": str(uuid.uuid4()),
            "reference_id": "",
            "sender": "portfolio_agent",
            "receiver": "orchestration_agent",
            "timestamp": datetime.utcnow().isoformat(),
            "response_type": "portfolio_update_response",
            "status": "success",
            "payload": {
                "portfolio_id": "default-portfolio",
                "successful": True
            }
        }
        
        # Set up the mock to return these responses in sequence
        mock_post.side_effect = [
            MockResponse(risk_response),
            MockResponse(portfolio_check_response),
            MockResponse(trade_response),
            MockResponse(portfolio_update_response)
        ]
        
        # Now simulate the workflow chain
        
        # 1. Risk assessment
        risk_message = self.base_message.copy()
        risk_message.update({
            "receiver": "market_analysis_agent",
            "request_type": "risk_assessment_request",
            "payload": {"asset": "BTC", "amount": 1000, "side": "BUY"}
        })
        risk_result = self.send_a2a_message(
            self.agent_endpoints["market_analysis_agent"],
            risk_message
        )
        
        # 2. Portfolio check
        portfolio_check_message = self.base_message.copy()
        portfolio_check_message.update({
            "receiver": "portfolio_agent",
            "request_type": "portfolio_check_request",
            "payload": {"portfolio_id": "default-portfolio", "required_funds": {"USD": 1000}}
        })
        portfolio_check_result = self.send_a2a_message(
            self.agent_endpoints["portfolio_agent"],
            portfolio_check_message
        )
        
        # 3. Execute trade
        trade_message = self.base_message.copy()
        trade_message.update({
            "receiver": "trade_execution_agent",
            "request_type": "execute_trade_request",
            "payload": {
                "asset": "BTC",
                "order_type": "MARKET",
                "side": "BUY",
                "amount": 1000,
                "is_amount_in_usd": True
            }
        })
        trade_result = self.send_a2a_message(
            self.agent_endpoints["trade_execution_agent"],
            trade_message
        )
        
        # 4. Update portfolio
        update_message = self.base_message.copy()
        update_message.update({
            "receiver": "portfolio_agent",
            "request_type": "portfolio_update_request",
            "payload": {
                "portfolio_id": "default-portfolio",
                "asset": "BTC",
                "transaction_type": "BUY",
                "amount": 0.017113,  # 1000 USD worth of BTC at 58432.15
                "price": 58432.15,
                "order_id": order_id
            }
        })
        update_result = self.send_a2a_message(
            self.agent_endpoints["portfolio_agent"],
            update_message
        )
        
        # Verify all steps in the chain were successful
        self.assertEqual(risk_result["status"], "success")
        self.assertEqual(portfolio_check_result["status"], "success")
        self.assertEqual(trade_result["status"], "success")
        self.assertEqual(update_result["status"], "success")
        
        # Verify mock was called the right number of times
        self.assertEqual(mock_post.call_count, 4)
    
    @patch('requests.post')
    def test_a2a_error_handling(self, mock_post):
        """Test handling of error responses in the A2A protocol"""
        # Configure mock response for an error
        mock_response = {
            "message_id": str(uuid.uuid4()),
            "reference_id": "",
            "sender": "trade_execution_agent",
            "receiver": "orchestration_agent",
            "timestamp": datetime.utcnow().isoformat(),
            "response_type": "execute_trade_response",
            "status": "error",
            "error": {
                "code": "INSUFFICIENT_FUNDS",
                "message": "Insufficient funds for the requested trade",
                "details": {
                    "required": 1000.0,
                    "available": 500.0,
                    "asset": "USD"
                }
            }
        }
        mock_post.return_value = MockResponse(mock_response)
        
        # Create a trade execution request that will fail
        message = self.base_message.copy()
        message.update({
            "receiver": "trade_execution_agent",
            "request_type": "execute_trade_request",
            "payload": {
                "asset": "BTC",
                "order_type": "MARKET",
                "side": "BUY",
                "amount": 1000,
                "is_amount_in_usd": True
            }
        })
        
        # Send the message
        response = self.send_a2a_message(
            self.agent_endpoints["trade_execution_agent"],
            message
        )
        
        # Verify the error structure
        self.assertEqual(response["status"], "error")
        self.assertIn("error", response)
        self.assertIn("code", response["error"])
        self.assertIn("message", response["error"])
        self.assertEqual(response["error"]["code"], "INSUFFICIENT_FUNDS")
    
    @patch('requests.post')
    def test_a2a_idempotency(self, mock_post):
        """Test idempotency of A2A protocol with duplicate message IDs"""
        # First response
        first_response = {
            "message_id": str(uuid.uuid4()),
            "reference_id": "",
            "sender": "trade_execution_agent",
            "receiver": "orchestration_agent",
            "timestamp": datetime.utcnow().isoformat(),
            "response_type": "execute_trade_response",
            "status": "success",
            "payload": {
                "order_id": f"ord_{uuid.uuid4().hex[:12]}",
                "status": "FILLED"
            }
        }
        
        # Duplicate response - identical except for message_id
        duplicate_response = first_response.copy()
        duplicate_response["message_id"] = str(uuid.uuid4())
        
        # Set up the mock to return these responses in sequence
        mock_post.side_effect = [
            MockResponse(first_response),
            MockResponse(duplicate_response)
        ]
        
        # Create a message with a persistent ID
        idempotent_id = str(uuid.uuid4())
        message = self.base_message.copy()
        message["message_id"] = idempotent_id
        message.update({
            "receiver": "trade_execution_agent",
            "request_type": "execute_trade_request",
            "payload": {
                "asset": "BTC",
                "order_type": "MARKET",
                "side": "BUY",
                "amount": 0.5,
                "is_amount_in_crypto": True,
                "idempotency_key": idempotent_id  # Include the ID as an idempotency key
            }
        })
        
        # Send the message twice with the same ID
        response1 = self.send_a2a_message(
            self.agent_endpoints["trade_execution_agent"],
            message
        )
        
        response2 = self.send_a2a_message(
            self.agent_endpoints["trade_execution_agent"],
            message
        )
        
        # Both responses should have the same order_id because they represent the same operation
        self.assertEqual(response1["payload"]["order_id"], response2["payload"]["order_id"])
        
        # Verify the idempotency key was sent in the request
        call_args_list = mock_post.call_args_list
        self.assertEqual(len(call_args_list), 2)
        
        # Check both calls had the same idempotency key
        for call_args in call_args_list:
            sent_data = json.loads(call_args[1]['data'])
            self.assertEqual(sent_data["message_id"], idempotent_id)
            self.assertEqual(sent_data["payload"]["idempotency_key"], idempotent_id)
    
    # Helper method to simulate sending A2A messages
    def send_a2a_message(self, endpoint, message):
        """
        Simulate sending an agent-to-agent message
        
        Args:
            endpoint (str): URL of the receiving agent
            message (dict): Message in A2A format
            
        Returns:
            dict: Response message from the agent
        """
        # In a real implementation, this would send the HTTP request
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            endpoint + "/api/a2a",
            data=json.dumps(message),
            headers=headers
        )
        
        # Return parsed response
        return response.json()


if __name__ == '__main__':
    unittest.main() 