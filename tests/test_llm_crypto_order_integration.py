"""
LLM Integration Tests for Crypto Order Workflow

This module simulates how an LLM agent would use functions to interact with the MCP client
and server to execute cryptocurrency orders using the workflow system.
"""
import unittest
from unittest.mock import patch, MagicMock, call
import json
import uuid
import subprocess
from datetime import datetime

from src.workflows.crypto_order_workflow import (
    get_workflow,
    simulate_step_execution,
    CryptoOrderWorkflow
)


class TestLLMCryptoOrderIntegration(unittest.TestCase):
    """Test cases for LLM integration with crypto order workflows"""
    
    def setUp(self):
        """Set up test data and mocks"""
        self.server_url = "http://localhost:8005"
        self.mcp_client_path = "mcp_client_hostname.py"
        
        # Sample data for a market order
        self.market_order_data = {
            "asset": "BTC",
            "order_type": "MARKET",
            "side": "BUY",
            "amount": 1000,
            "is_amount_in_usd": True,
            "portfolio_id": "default-portfolio"
        }
        
        # Sample data for a limit order
        self.limit_order_data = {
            "asset": "ETH",
            "order_type": "LIMIT",
            "side": "SELL",
            "amount": 2.5,
            "is_amount_in_usd": False,
            "price": 2850.00,
            "portfolio_id": "default-portfolio"
        }
        
        # Simulate agent info that would be retrieved from the server
        self.agent_info = {
            "status": {
                "Market Analysis Agent": {
                    "status": "online",
                    "version": "1.0.0",
                    "capabilities": ["market_analysis", "risk_assessment"],
                    "url": "http://market-analysis-agent:8001"
                },
                "Trade Execution Agent": {
                    "status": "online",
                    "version": "1.0.0",
                    "capabilities": ["execute_trade", "get_order_status"],
                    "url": "http://trade-execution-agent:8002"
                },
                "Risk Management Agent": {
                    "status": "online",
                    "version": "1.0.0",
                    "capabilities": ["assess_trade_risk", "monitor_portfolio_risk"],
                    "url": "http://risk-management-agent:8003"
                },
                "Reporting and Analytics Agent": {
                    "status": "online",
                    "version": "1.0.0",
                    "capabilities": ["generate_performance_report", "generate_portfolio_valuation"],
                    "url": "http://reporting-analytics-agent:8004"
                }
            }
        }
    
    @patch('subprocess.run')
    def test_llm_function_check_agents_status(self, mock_run):
        """Test LLM function to check agent status using MCP client"""
        # Mock the subprocess.run result
        mock_process = MagicMock()
        mock_process.stdout = json.dumps(self.agent_info).encode('utf-8')
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Simulate LLM calling a function to check agent status
        result = self.llm_function_check_agents(self.server_url)
        
        # Verify the result
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0]["name"], "Market Analysis Agent")
        self.assertEqual(result[1]["name"], "Trade Execution Agent")
        self.assertEqual(result[2]["name"], "Risk Management Agent")
        self.assertEqual(result[3]["name"], "Reporting and Analytics Agent")
        
        # Verify all agents are online
        for agent in result:
            self.assertEqual(agent["status"], "online")
        
        # Verify mock was called correctly
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        self.assertEqual(kwargs['capture_output'], True)
        self.assertEqual(kwargs['text'], False)
        cmd = kwargs['args']
        self.assertIn(self.mcp_client_path, cmd)
        self.assertIn("--server", cmd)
        self.assertIn(self.server_url, cmd)
        self.assertIn("agents", cmd)
    
    @patch('subprocess.run')
    def test_llm_function_create_market_order(self, mock_run):
        """Test LLM function to create a market order"""
        # Mock the subprocess response for workflow creation
        workflow_id = f"crypto-order-{uuid.uuid4()}"
        mock_response = {
            "status": "success",
            "workflow_id": workflow_id,
            "message": "Workflow created successfully",
            "execution_status": "PENDING"
        }
        
        mock_process = MagicMock()
        mock_process.stdout = json.dumps(mock_response).encode('utf-8')
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Simulate LLM calling a function to create a market order
        result = self.llm_function_create_order(
            server_url=self.server_url,
            asset="BTC",
            order_type="MARKET",
            side="BUY",
            amount=1000,
            is_amount_in_usd=True
        )
        
        # Verify the result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["workflow_id"], workflow_id)
        
        # Verify mock was called correctly
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        self.assertEqual(kwargs['capture_output'], True)
        self.assertEqual(kwargs['text'], False)
        cmd = kwargs['args']
        
        # Check command format
        self.assertIn(self.mcp_client_path, cmd)
        self.assertIn("--server", cmd)
        self.assertIn(self.server_url, cmd)
        self.assertIn("create-workflow", cmd)
        self.assertIn("crypto_order", cmd)
        
        # Parameters should be included
        cmd_str = " ".join(cmd)
        self.assertIn("asset=BTC", cmd_str)
        self.assertIn("order_type=MARKET", cmd_str)
        self.assertIn("side=BUY", cmd_str)
        self.assertIn("amount=1000", cmd_str)
        self.assertIn("is_amount_in_usd=True", cmd_str)
    
    @patch('subprocess.run')
    def test_llm_function_create_limit_order(self, mock_run):
        """Test LLM function to create a limit order"""
        # Mock the subprocess response for workflow creation
        workflow_id = f"crypto-order-{uuid.uuid4()}"
        mock_response = {
            "status": "success",
            "workflow_id": workflow_id,
            "message": "Workflow created successfully",
            "execution_status": "PENDING"
        }
        
        mock_process = MagicMock()
        mock_process.stdout = json.dumps(mock_response).encode('utf-8')
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Simulate LLM calling a function to create a limit order
        result = self.llm_function_create_order(
            server_url=self.server_url,
            asset="ETH",
            order_type="LIMIT",
            side="SELL",
            amount=2.5,
            is_amount_in_usd=False,
            price=2850.00
        )
        
        # Verify the result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["workflow_id"], workflow_id)
        
        # Verify mock was called correctly
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        cmd = kwargs['args']
        
        # Check parameters specific to limit orders
        cmd_str = " ".join(cmd)
        self.assertIn("asset=ETH", cmd_str)
        self.assertIn("order_type=LIMIT", cmd_str)
        self.assertIn("side=SELL", cmd_str)
        self.assertIn("amount=2.5", cmd_str)
        self.assertIn("is_amount_in_usd=False", cmd_str)
        self.assertIn("price=2850.0", cmd_str)
    
    @patch('subprocess.run')
    def test_llm_function_check_order_status(self, mock_run):
        """Test LLM function to check the status of an order workflow"""
        # Create a workflow ID
        workflow_id = f"crypto-order-{uuid.uuid4()}"
        
        # Mock the subprocess response for workflow status
        mock_response = {
            "status": "success",
            "workflow": {
                "workflow_id": workflow_id,
                "name": "Crypto Order",
                "status": "RUNNING",
                "created_at": datetime.now().isoformat(),
                "steps": [
                    {
                        "step_id": "validate_order_params",
                        "agent_id": "validation_agent",
                        "status": "COMPLETED"
                    },
                    {
                        "step_id": "check_available_funds",
                        "agent_id": "portfolio_agent",
                        "status": "COMPLETED"
                    },
                    {
                        "step_id": "calculate_order_details",
                        "agent_id": "order_calculation_agent",
                        "status": "RUNNING"
                    },
                    {
                        "step_id": "submit_order",
                        "agent_id": "exchange_agent",
                        "status": "PENDING"
                    },
                    {
                        "step_id": "monitor_order_status",
                        "agent_id": "exchange_agent",
                        "status": "PENDING"
                    },
                    {
                        "step_id": "update_portfolio",
                        "agent_id": "portfolio_agent",
                        "status": "PENDING"
                    }
                ],
                "parameters": self.market_order_data
            }
        }
        
        mock_process = MagicMock()
        mock_process.stdout = json.dumps(mock_response).encode('utf-8')
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Simulate LLM calling a function to check order status
        result = self.llm_function_check_order_status(
            server_url=self.server_url,
            workflow_id=workflow_id
        )
        
        # Verify the result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["workflow_status"], "RUNNING")
        self.assertEqual(len(result["steps"]), 6)
        self.assertEqual(result["steps"][0]["status"], "COMPLETED")
        self.assertEqual(result["steps"][1]["status"], "COMPLETED")
        self.assertEqual(result["steps"][2]["status"], "RUNNING")
        
        # Verify mock was called correctly
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        cmd = kwargs['args']
        
        # Check command format
        self.assertIn(self.mcp_client_path, cmd)
        self.assertIn("--server", cmd)
        self.assertIn(self.server_url, cmd)
        self.assertIn("get-workflow", cmd)
        self.assertIn(workflow_id, cmd)
    
    @patch('subprocess.run')
    def test_llm_function_get_order_result(self, mock_run):
        """Test LLM function to get the final result of a completed order"""
        # Create a workflow ID
        workflow_id = f"crypto-order-{uuid.uuid4()}"
        order_id = f"ord_{uuid.uuid4().hex[:12]}"
        
        # Mock the subprocess response for a completed workflow
        mock_response = {
            "status": "success",
            "workflow": {
                "workflow_id": workflow_id,
                "name": "Crypto Order",
                "status": "COMPLETED",
                "created_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat(),
                "steps": [
                    {
                        "step_id": "validate_order_params",
                        "agent_id": "validation_agent",
                        "status": "COMPLETED",
                        "result": {
                            "validation_result": {"valid": True}
                        }
                    },
                    {
                        "step_id": "check_available_funds",
                        "agent_id": "portfolio_agent",
                        "status": "COMPLETED",
                        "result": {
                            "funds_check": {"sufficient_funds": True}
                        }
                    },
                    {
                        "step_id": "calculate_order_details",
                        "agent_id": "order_calculation_agent",
                        "status": "COMPLETED",
                        "result": {
                            "order_details": {
                                "amount_crypto": 0.017113,
                                "amount_usd": 1000,
                                "price": 58432.15
                            }
                        }
                    },
                    {
                        "step_id": "submit_order",
                        "agent_id": "exchange_agent",
                        "status": "COMPLETED",
                        "result": {
                            "order_submission": {
                                "order_id": order_id,
                                "status": "FILLED"
                            }
                        }
                    },
                    {
                        "step_id": "monitor_order_status",
                        "agent_id": "exchange_agent",
                        "status": "COMPLETED",
                        "result": {
                            "order_status": {
                                "status": "FILLED",
                                "filled_amount": 0.017113
                            }
                        }
                    },
                    {
                        "step_id": "update_portfolio",
                        "agent_id": "portfolio_agent",
                        "status": "COMPLETED",
                        "result": {
                            "portfolio_update": {
                                "successful": True,
                                "new_balances": {
                                    "BTC": 0.517113,
                                    "USD": 24000.50  # 25000.50 - 1000
                                }
                            }
                        }
                    }
                ],
                "parameters": self.market_order_data
            }
        }
        
        mock_process = MagicMock()
        mock_process.stdout = json.dumps(mock_response).encode('utf-8')
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Simulate LLM calling a function to get order results
        result = self.llm_function_get_order_result(
            server_url=self.server_url,
            workflow_id=workflow_id
        )
        
        # Verify the result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["order_status"], "COMPLETED")
        self.assertEqual(result["order_details"]["asset"], "BTC")
        self.assertEqual(result["order_details"]["side"], "BUY")
        self.assertEqual(result["order_details"]["amount_usd"], 1000)
        self.assertAlmostEqual(result["order_details"]["amount_crypto"], 0.017113)
        self.assertEqual(result["order_details"]["order_id"], order_id)
        self.assertEqual(result["portfolio_update"]["new_balances"]["BTC"], 0.517113)
        
        # Verify mock was called correctly
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_llm_function_cancel_order(self, mock_run):
        """Test LLM function to cancel an order workflow"""
        # Create a workflow ID
        workflow_id = f"crypto-order-{uuid.uuid4()}"
        
        # Mock the subprocess response for workflow cancellation
        mock_response = {
            "status": "success",
            "message": "Workflow cancelled successfully",
            "workflow_id": workflow_id,
            "workflow_status": "CANCELLED"
        }
        
        mock_process = MagicMock()
        mock_process.stdout = json.dumps(mock_response).encode('utf-8')
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Simulate LLM calling a function to cancel an order
        result = self.llm_function_cancel_order(
            server_url=self.server_url,
            workflow_id=workflow_id
        )
        
        # Verify the result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["workflow_status"], "CANCELLED")
        
        # Verify mock was called correctly
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        cmd = kwargs['args']
        
        # Check command format
        self.assertIn(self.mcp_client_path, cmd)
        self.assertIn("--server", cmd)
        self.assertIn(self.server_url, cmd)
        self.assertIn("cancel-workflow", cmd)
        self.assertIn(workflow_id, cmd)
    
    @patch('subprocess.run')
    def test_llm_conversation_market_order_flow(self, mock_run):
        """Test a complete conversation flow where LLM creates and monitors a market order"""
        # Workflow ID for the test
        workflow_id = f"crypto-order-{uuid.uuid4()}"
        order_id = f"ord_{uuid.uuid4().hex[:12]}"
        
        # Prepare a sequence of mock responses for different calls
        mock_responses = [
            # First call: create order
            {
                "status": "success",
                "workflow_id": workflow_id,
                "message": "Workflow created successfully",
                "execution_status": "PENDING"
            },
            # Second call: check order status (running)
            {
                "status": "success",
                "workflow": {
                    "workflow_id": workflow_id,
                    "status": "RUNNING",
                    "steps": [
                        {"step_id": "validate_order_params", "status": "COMPLETED"},
                        {"step_id": "check_available_funds", "status": "COMPLETED"},
                        {"step_id": "calculate_order_details", "status": "RUNNING"},
                        {"step_id": "submit_order", "status": "PENDING"},
                        {"step_id": "monitor_order_status", "status": "PENDING"},
                        {"step_id": "update_portfolio", "status": "PENDING"}
                    ]
                }
            },
            # Third call: check order status (completed)
            {
                "status": "success",
                "workflow": {
                    "workflow_id": workflow_id,
                    "status": "COMPLETED",
                    "steps": [
                        {"step_id": "validate_order_params", "status": "COMPLETED"},
                        {"step_id": "check_available_funds", "status": "COMPLETED"},
                        {"step_id": "calculate_order_details", "status": "COMPLETED"},
                        {"step_id": "submit_order", "status": "COMPLETED", 
                         "result": {"order_submission": {"order_id": order_id}}},
                        {"step_id": "monitor_order_status", "status": "COMPLETED"},
                        {"step_id": "update_portfolio", "status": "COMPLETED", 
                         "result": {"portfolio_update": {"successful": True}}}
                    ]
                }
            }
        ]
        
        # Configure mock to return different responses for each call
        side_effects = []
        for response in mock_responses:
            mock_proc = MagicMock()
            mock_proc.stdout = json.dumps(response).encode('utf-8')
            mock_proc.returncode = 0
            side_effects.append(mock_proc)
        
        mock_run.side_effect = side_effects
        
        # Simulate LLM conversation flow
        
        # 1. User asks to buy BTC
        response1 = self.llm_function_create_order(
            server_url=self.server_url,
            asset="BTC",
            order_type="MARKET",
            side="BUY",
            amount=1000,
            is_amount_in_usd=True
        )
        
        # Assert workflow was created
        self.assertEqual(response1["status"], "success")
        self.assertEqual(response1["workflow_id"], workflow_id)
        
        # 2. User asks for status update
        response2 = self.llm_function_check_order_status(
            server_url=self.server_url,
            workflow_id=workflow_id
        )
        
        # Assert workflow is running
        self.assertEqual(response2["status"], "success")
        self.assertEqual(response2["workflow_status"], "RUNNING")
        
        # 3. User asks for final result
        response3 = self.llm_function_check_order_status(
            server_url=self.server_url,
            workflow_id=workflow_id
        )
        
        # Assert workflow completed
        self.assertEqual(response3["status"], "success")
        self.assertEqual(response3["workflow_status"], "COMPLETED")
        
        # Verify all expected calls were made
        self.assertEqual(mock_run.call_count, 3)
        
        # Check if the calls were made in the right order with right commands
        calls = mock_run.call_args_list
        self.assertIn("create-workflow", " ".join(calls[0][1]['args']))
        self.assertIn("get-workflow", " ".join(calls[1][1]['args']))
        self.assertIn("get-workflow", " ".join(calls[2][1]['args']))
    
    # Simulated LLM function implementation
    
    def llm_function_check_agents(self, server_url):
        """
        Function for an LLM to check the status of all agents in the system.
        
        Args:
            server_url (str): URL of the MCP server
            
        Returns:
            list: List of agents with their status and capabilities
        """
        cmd = [
            "python", self.mcp_client_path,
            "--server", server_url,
            "agents"
        ]
        
        process = subprocess.run(
            args=cmd,
            capture_output=True,
            text=False
        )
        
        if process.returncode != 0:
            return {
                "status": "error",
                "message": "Failed to get agent status"
            }
        
        # Parse JSON response
        response = json.loads(process.stdout.decode('utf-8'))
        
        # Format agent information for LLM
        agents = []
        for name, info in response["status"].items():
            agents.append({
                "name": name,
                "status": info["status"],
                "capabilities": info["capabilities"],
                "url": info["url"]
            })
        
        return agents
    
    def llm_function_create_order(self, server_url, asset, order_type, side, amount, 
                                is_amount_in_usd=True, price=None, portfolio_id="default-portfolio"):
        """
        Function for an LLM to create a new crypto order workflow.
        
        Args:
            server_url (str): URL of the MCP server
            asset (str): Asset symbol (e.g., BTC, ETH)
            order_type (str): MARKET or LIMIT
            side (str): BUY or SELL
            amount (float): Amount to buy/sell
            is_amount_in_usd (bool): Whether amount is in USD
            price (float, optional): Limit price (required for LIMIT orders)
            portfolio_id (str): Portfolio ID
            
        Returns:
            dict: Response with workflow_id and status
        """
        # Construct command
        cmd = [
            "python", self.mcp_client_path,
            "--server", server_url,
            "create-workflow", "crypto_order",
            f"asset={asset}",
            f"order_type={order_type}",
            f"side={side}",
            f"amount={amount}",
            f"is_amount_in_usd={is_amount_in_usd}",
            f"portfolio_id={portfolio_id}"
        ]
        
        # Add price for limit orders
        if order_type == "LIMIT" and price is not None:
            cmd.append(f"price={price}")
        
        # Execute command
        process = subprocess.run(
            args=cmd,
            capture_output=True,
            text=False
        )
        
        if process.returncode != 0:
            return {
                "status": "error",
                "message": "Failed to create order workflow"
            }
        
        # Parse JSON response
        response = json.loads(process.stdout.decode('utf-8'))
        
        return response
    
    def llm_function_check_order_status(self, server_url, workflow_id):
        """
        Function for an LLM to check the status of an order workflow.
        
        Args:
            server_url (str): URL of the MCP server
            workflow_id (str): ID of the workflow to check
            
        Returns:
            dict: Workflow status information
        """
        cmd = [
            "python", self.mcp_client_path,
            "--server", server_url,
            "get-workflow", workflow_id
        ]
        
        process = subprocess.run(
            args=cmd,
            capture_output=True,
            text=False
        )
        
        if process.returncode != 0:
            return {
                "status": "error",
                "message": "Failed to get workflow status"
            }
        
        # Parse JSON response
        response = json.loads(process.stdout.decode('utf-8'))
        
        # Format for LLM consumption
        if response["status"] == "success":
            workflow = response["workflow"]
            result = {
                "status": "success",
                "workflow_id": workflow["workflow_id"],
                "workflow_status": workflow["status"],
                "steps": []
            }
            
            # Format steps
            for step in workflow["steps"]:
                result["steps"].append({
                    "step_id": step["step_id"],
                    "status": step["status"]
                })
            
            return result
        
        return response
    
    def llm_function_get_order_result(self, server_url, workflow_id):
        """
        Function for an LLM to get detailed results of a completed order.
        
        Args:
            server_url (str): URL of the MCP server
            workflow_id (str): ID of the workflow to check
            
        Returns:
            dict: Detailed order information and results
        """
        cmd = [
            "python", self.mcp_client_path,
            "--server", server_url,
            "get-workflow", workflow_id
        ]
        
        process = subprocess.run(
            args=cmd,
            capture_output=True,
            text=False
        )
        
        if process.returncode != 0:
            return {
                "status": "error",
                "message": "Failed to get order results"
            }
        
        # Parse JSON response
        response = json.loads(process.stdout.decode('utf-8'))
        
        # Format response for LLM consumption
        if response["status"] == "success":
            workflow = response["workflow"]
            parameters = workflow["parameters"]
            
            result = {
                "status": "success",
                "order_status": workflow["status"],
                "order_details": {
                    "asset": parameters["asset"],
                    "order_type": parameters["order_type"],
                    "side": parameters["side"],
                    "amount_usd": parameters["amount"] if parameters.get("is_amount_in_usd", True) else None,
                    "amount_crypto": None,
                    "price": parameters.get("price"),
                    "order_id": None
                },
                "portfolio_update": None
            }
            
            # Extract information from step results
            for step in workflow["steps"]:
                if step["step_id"] == "calculate_order_details" and "result" in step:
                    details = step["result"].get("order_details", {})
                    result["order_details"]["amount_crypto"] = details.get("amount_crypto")
                    
                elif step["step_id"] == "submit_order" and "result" in step:
                    submission = step["result"].get("order_submission", {})
                    result["order_details"]["order_id"] = submission.get("order_id")
                    
                elif step["step_id"] == "update_portfolio" and "result" in step:
                    result["portfolio_update"] = step["result"].get("portfolio_update")
            
            return result
        
        return response
    
    def llm_function_cancel_order(self, server_url, workflow_id):
        """
        Function for an LLM to cancel an in-progress order workflow.
        
        Args:
            server_url (str): URL of the MCP server
            workflow_id (str): ID of the workflow to cancel
            
        Returns:
            dict: Cancellation status
        """
        cmd = [
            "python", self.mcp_client_path,
            "--server", server_url,
            "cancel-workflow", workflow_id
        ]
        
        process = subprocess.run(
            args=cmd,
            capture_output=True,
            text=False
        )
        
        if process.returncode != 0:
            return {
                "status": "error",
                "message": "Failed to cancel workflow"
            }
        
        # Parse JSON response
        response = json.loads(process.stdout.decode('utf-8'))
        return response


if __name__ == '__main__':
    unittest.main() 