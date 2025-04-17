"""
Unit Tests for Crypto Order Workflow

This module contains tests for both the legacy and OOP implementations
of the crypto order workflow.
"""
import unittest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime
import uuid

from src.workflows.crypto_order_workflow import (
    get_workflow,
    simulate_step_execution,
    CryptoOrderWorkflow,
    create_crypto_order_workflow
)


class TestCryptoOrderWorkflowLegacy(unittest.TestCase):
    """Tests for the legacy implementation of crypto order workflow"""
    
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
        
        self.limit_order_parameters = {
            "asset": "ETH",
            "order_type": "LIMIT",
            "side": "SELL",
            "amount": 2.5,
            "is_amount_in_usd": False,
            "price": 2850.00,
            "portfolio_id": "test-portfolio"
        }
    
    def test_get_workflow_market_order(self):
        """Test creating a market order workflow"""
        workflow = get_workflow(self.valid_parameters)
        
        # Check workflow creation
        self.assertIsNotNone(workflow)
        self.assertEqual(workflow.name, "Crypto Order")
        self.assertEqual(len(workflow.steps), 6)
        
        # Check steps
        step_names = [step.agent_id for step in workflow.steps]
        self.assertEqual(step_names, [
            "validation_agent",
            "portfolio_agent",
            "order_calculation_agent",
            "exchange_agent",
            "exchange_agent",
            "portfolio_agent"
        ])
        
        # Check parameters
        self.assertEqual(workflow.parameters["asset"], "BTC")
        self.assertEqual(workflow.parameters["order_type"], "MARKET")
        self.assertEqual(workflow.parameters["side"], "BUY")
        self.assertEqual(workflow.parameters["amount"], 1000)
    
    def test_get_workflow_limit_order(self):
        """Test creating a limit order workflow"""
        workflow = get_workflow(self.limit_order_parameters)
        
        # Check parameters
        self.assertEqual(workflow.parameters["asset"], "ETH")
        self.assertEqual(workflow.parameters["order_type"], "LIMIT")
        self.assertEqual(workflow.parameters["side"], "SELL")
        self.assertEqual(workflow.parameters["amount"], 2.5)
        self.assertEqual(workflow.parameters["price"], 2850.00)
    
    def test_get_workflow_missing_required_params(self):
        """Test error handling for missing parameters"""
        # Missing asset
        invalid_params = self.valid_parameters.copy()
        del invalid_params["asset"]
        with self.assertRaises(ValueError) as context:
            get_workflow(invalid_params)
        self.assertIn("Missing required parameter: asset", str(context.exception))
        
        # Missing order_type
        invalid_params = self.valid_parameters.copy()
        del invalid_params["order_type"]
        with self.assertRaises(ValueError) as context:
            get_workflow(invalid_params)
        self.assertIn("Missing required parameter: order_type", str(context.exception))
    
    def test_get_workflow_invalid_order_type(self):
        """Test error handling for invalid order type"""
        invalid_params = self.valid_parameters.copy()
        invalid_params["order_type"] = "STOP_LIMIT"  # Not supported
        with self.assertRaises(ValueError) as context:
            get_workflow(invalid_params)
        self.assertIn("Invalid order_type", str(context.exception))
    
    def test_get_workflow_invalid_side(self):
        """Test error handling for invalid side"""
        invalid_params = self.valid_parameters.copy()
        invalid_params["side"] = "HOLD"  # Not supported
        with self.assertRaises(ValueError) as context:
            get_workflow(invalid_params)
        self.assertIn("Invalid side", str(context.exception))
    
    def test_get_workflow_invalid_amount(self):
        """Test error handling for invalid amount"""
        # Negative amount
        invalid_params = self.valid_parameters.copy()
        invalid_params["amount"] = -100
        with self.assertRaises(ValueError) as context:
            get_workflow(invalid_params)
        self.assertIn("Amount must be greater than zero", str(context.exception))
        
        # Non-numeric amount
        invalid_params = self.valid_parameters.copy()
        invalid_params["amount"] = "not_a_number"
        with self.assertRaises(ValueError) as context:
            get_workflow(invalid_params)
        self.assertIn("Amount must be a positive number", str(context.exception))
    
    def test_get_workflow_limit_order_missing_price(self):
        """Test error handling for limit order without price"""
        invalid_params = self.valid_parameters.copy()
        invalid_params["order_type"] = "LIMIT"
        with self.assertRaises(ValueError) as context:
            get_workflow(invalid_params)
        self.assertIn("Price is required for LIMIT orders", str(context.exception))
    
    def test_simulate_step_execution_validate_order_params(self):
        """Test simulating the validate order params step"""
        step_id = "validate_order_params"
        context = {}
        
        result = simulate_step_execution(step_id, self.valid_parameters, context)
        
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["step_id"], step_id)
        self.assertIn("validation_result", result)
        self.assertTrue(result["validation_result"]["valid"])
        self.assertTrue(result["validation_result"]["asset_exists"])
        self.assertTrue(result["validation_result"]["asset_active"])
    
    def test_simulate_step_execution_check_available_funds(self):
        """Test simulating the check available funds step"""
        step_id = "check_available_funds"
        context = {}
        
        result = simulate_step_execution(step_id, self.valid_parameters, context)
        
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["step_id"], step_id)
        self.assertIn("funds_check", result)
        self.assertTrue(result["funds_check"]["sufficient_funds"])
        self.assertEqual(result["funds_check"]["portfolio_id"], "test-portfolio")
    
    def test_simulate_step_execution_calculate_order_details(self):
        """Test simulating the calculate order details step"""
        step_id = "calculate_order_details"
        context = {}
        
        result = simulate_step_execution(step_id, self.valid_parameters, context)
        
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["step_id"], step_id)
        self.assertIn("order_details", result)
        self.assertEqual(result["order_details"]["asset"], "BTC")
        self.assertEqual(result["order_details"]["side"], "BUY")
        self.assertEqual(result["order_details"]["order_type"], "MARKET")
        self.assertGreater(result["order_details"]["amount_crypto"], 0)
        self.assertEqual(result["order_details"]["amount_usd"], 1000)
    
    def test_simulate_step_execution_submit_order(self):
        """Test simulating the submit order step"""
        step_id = "submit_order"
        # Create context with previous step results
        context = {
            "calculate_order_details": {
                "order_details": {
                    "asset": "BTC",
                    "order_type": "MARKET",
                    "side": "BUY",
                    "price": 58432.15,
                    "amount_crypto": 0.017113,
                    "market_price": 58432.15
                }
            }
        }
        
        result = simulate_step_execution(step_id, self.valid_parameters, context)
        
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["step_id"], step_id)
        self.assertIn("order_submission", result)
        self.assertTrue(result["order_submission"]["success"])
        self.assertEqual(result["order_submission"]["status"], "FILLED")  # Market orders fill immediately
        self.assertEqual(result["order_submission"]["remaining_amount"], 0.0)
    
    def test_simulate_step_execution_monitor_order_status(self):
        """Test simulating the monitor order status step"""
        step_id = "monitor_order_status"
        # Create context with previous step results
        context = {
            "submit_order": {
                "order_submission": {
                    "order_id": "ord_123456789abc",
                    "order_type": "MARKET",
                    "size": 0.017113,
                    "price": 58432.15
                }
            }
        }
        
        result = simulate_step_execution(step_id, self.valid_parameters, context)
        
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["step_id"], step_id)
        self.assertIn("order_status", result)
        self.assertEqual(result["order_status"]["status"], "FILLED")
        self.assertEqual(result["order_status"]["filled_amount"], 0.017113)
        self.assertEqual(result["order_status"]["remaining_amount"], 0.0)
        self.assertFalse(result["order_status"]["is_cancelable"])
    
    def test_simulate_step_execution_update_portfolio(self):
        """Test simulating the update portfolio step"""
        step_id = "update_portfolio"
        # Create context with previous step results
        context = {
            "calculate_order_details": {
                "order_details": {
                    "asset": "BTC",
                    "side": "BUY",
                    "amount_crypto": 0.017113
                }
            },
            "monitor_order_status": {
                "order_status": {
                    "order_id": "ord_123456789abc",
                    "filled_amount": 0.017113,
                    "fill_price": 58432.15
                }
            }
        }
        
        result = simulate_step_execution(step_id, self.valid_parameters, context)
        
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["step_id"], step_id)
        self.assertIn("portfolio_update", result)
        self.assertTrue(result["portfolio_update"]["successful"])
        self.assertEqual(result["portfolio_update"]["portfolio_id"], "test-portfolio")
        self.assertIn("BTC", result["portfolio_update"]["changes"])
        self.assertEqual(result["portfolio_update"]["changes"]["BTC"], 0.017113)
        self.assertLess(result["portfolio_update"]["changes"]["USD"], 0)  # Negative for buy


class TestCryptoOrderWorkflowOOP(unittest.TestCase):
    """Tests for the OOP implementation of crypto order workflow"""
    
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
        
        self.limit_order_parameters = {
            "asset": "ETH",
            "order_type": "LIMIT",
            "side": "SELL",
            "amount": 2.5,
            "is_amount_in_usd": False,
            "price": 2850.00,
            "portfolio_id": "test-portfolio"
        }
    
    def test_create_workflow(self):
        """Test creating a workflow through the helper function"""
        workflow = create_crypto_order_workflow(self.valid_parameters)
        
        # Check workflow creation
        self.assertIsNotNone(workflow)
        self.assertEqual(workflow.name, "Crypto Order")
        self.assertEqual(len(workflow.steps), 6)
    
    def test_workflow_init_and_steps(self):
        """Test initializing a workflow directly and checking steps"""
        workflow = CryptoOrderWorkflow(parameters=self.valid_parameters)
        
        # Check basic properties
        self.assertEqual(workflow.name, "Crypto Order")
        self.assertEqual(workflow.description, "Place and manage cryptocurrency orders")
        
        # Check steps
        self.assertEqual(len(workflow.steps), 6)
        step_names = [step.name for step in workflow.steps]
        self.assertEqual(step_names, [
            "Validate Order Parameters",
            "Check Available Funds",
            "Calculate Order Details",
            "Submit Order",
            "Monitor Order Status",
            "Update Portfolio"
        ])
    
    def test_validate_parameters_valid(self):
        """Test parameter validation with valid parameters"""
        workflow = CryptoOrderWorkflow(parameters=self.valid_parameters)
        self.assertTrue(workflow.validate_parameters())
        
        # Test limit order parameters
        workflow = CryptoOrderWorkflow(parameters=self.limit_order_parameters)
        self.assertTrue(workflow.validate_parameters())
    
    def test_validate_parameters_invalid(self):
        """Test parameter validation with invalid parameters"""
        # Missing asset
        invalid_params = self.valid_parameters.copy()
        del invalid_params["asset"]
        workflow = CryptoOrderWorkflow(parameters=invalid_params)
        self.assertFalse(workflow.validate_parameters())
        
        # Invalid order type
        invalid_params = self.valid_parameters.copy()
        invalid_params["order_type"] = "STOP_LIMIT"
        workflow = CryptoOrderWorkflow(parameters=invalid_params)
        self.assertFalse(workflow.validate_parameters())
        
        # Invalid side
        invalid_params = self.valid_parameters.copy()
        invalid_params["side"] = "HOLD"
        workflow = CryptoOrderWorkflow(parameters=invalid_params)
        self.assertFalse(workflow.validate_parameters())
        
        # Negative amount
        invalid_params = self.valid_parameters.copy()
        invalid_params["amount"] = -100
        workflow = CryptoOrderWorkflow(parameters=invalid_params)
        self.assertFalse(workflow.validate_parameters())
        
        # Limit order without price
        invalid_params = self.valid_parameters.copy()
        invalid_params["order_type"] = "LIMIT"
        workflow = CryptoOrderWorkflow(parameters=invalid_params)
        self.assertFalse(workflow.validate_parameters())
    
    def test_validate_order_params_step(self):
        """Test the validate order params step"""
        workflow = CryptoOrderWorkflow(parameters=self.valid_parameters)
        result = workflow._validate_order_params(self.valid_parameters)
        
        self.assertTrue(result["valid"])
        self.assertTrue(result["asset_exists"])
        self.assertTrue(result["asset_active"])
        self.assertTrue(result["trading_enabled"])
    
    def test_check_available_funds_step(self):
        """Test the check available funds step"""
        workflow = CryptoOrderWorkflow(parameters=self.valid_parameters)
        result = workflow._check_available_funds(self.valid_parameters)
        
        self.assertTrue(result["sufficient_funds"])
        self.assertEqual(result["portfolio_id"], "test-portfolio")
        self.assertGreater(result["available_usd"], 0)
        self.assertIn("BTC", result["available_crypto"])
    
    def test_calculate_order_details_step(self):
        """Test the calculate order details step"""
        workflow = CryptoOrderWorkflow(parameters=self.valid_parameters)
        result = workflow._calculate_order_details(self.valid_parameters)
        
        self.assertEqual(result["asset"], "BTC")
        self.assertEqual(result["order_type"], "MARKET")
        self.assertEqual(result["side"], "BUY")
        self.assertGreater(result["amount_crypto"], 0)
        self.assertEqual(result["amount_usd"], 1000)
        self.assertGreater(result["estimated_fee_usd"], 0)
    
    @patch.object(CryptoOrderWorkflow, '_calculate_order_details')
    def test_submit_order_step(self, mock_calculate):
        """Test the submit order step"""
        # Setup mock for previous step result
        mock_result = {
            "asset": "BTC",
            "order_type": "MARKET",
            "side": "BUY",
            "price": 58432.15,
            "amount_crypto": 0.017113,
            "market_price": 58432.15
        }
        mock_calculate.return_value = mock_result
        
        workflow = CryptoOrderWorkflow(parameters=self.valid_parameters)
        # Manually set the step result to simulate previous step execution
        workflow.steps[2].result = mock_result
        
        result = workflow._submit_order(self.valid_parameters)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["asset"], "BTC")
        self.assertEqual(result["order_type"], "MARKET")
        self.assertEqual(result["side"], "BUY")
        self.assertEqual(result["status"], "FILLED")  # Market orders fill immediately
    
    @patch.object(CryptoOrderWorkflow, '_submit_order')
    def test_monitor_order_status_step(self, mock_submit):
        """Test the monitor order status step"""
        # Setup mock for previous step result
        order_id = f"ord_{uuid.uuid4().hex[:12]}"
        mock_result = {
            "success": True,
            "order_id": order_id,
            "exchange": "binance",
            "asset": "BTC",
            "order_type": "MARKET",
            "side": "BUY",
            "price": 58432.15,
            "size": 0.017113,
            "status": "FILLED",
            "filled_amount": 0.017113,
            "remaining_amount": 0.0
        }
        mock_submit.return_value = mock_result
        
        workflow = CryptoOrderWorkflow(parameters=self.valid_parameters)
        # Manually set the step result to simulate previous step execution
        workflow.steps[3].result = mock_result
        
        result = workflow._monitor_order_status(self.valid_parameters)
        
        self.assertEqual(result["order_id"], order_id)
        self.assertEqual(result["status"], "FILLED")
        self.assertEqual(result["filled_amount"], 0.017113)
        self.assertEqual(result["remaining_amount"], 0.0)
        self.assertFalse(result["is_cancelable"])
    
    @patch.object(CryptoOrderWorkflow, '_calculate_order_details')
    @patch.object(CryptoOrderWorkflow, '_monitor_order_status')
    def test_update_portfolio_step(self, mock_monitor, mock_calculate):
        """Test the update portfolio step"""
        # Setup mocks for previous step results
        calculate_result = {
            "asset": "BTC",
            "order_type": "MARKET",
            "side": "BUY",
            "price": 58432.15,
            "amount_crypto": 0.017113,
            "market_price": 58432.15
        }
        mock_calculate.return_value = calculate_result
        
        monitor_result = {
            "order_id": f"ord_{uuid.uuid4().hex[:12]}",
            "status": "FILLED",
            "filled_amount": 0.017113,
            "remaining_amount": 0.0,
            "fill_price": 58432.15
        }
        mock_monitor.return_value = monitor_result
        
        workflow = CryptoOrderWorkflow(parameters=self.valid_parameters)
        # Manually set the step results to simulate previous step execution
        workflow.steps[2].result = calculate_result
        workflow.steps[4].result = monitor_result
        
        result = workflow._update_portfolio(self.valid_parameters)
        
        self.assertTrue(result["successful"])
        self.assertEqual(result["portfolio_id"], "test-portfolio")
        self.assertIn("BTC", result["changes"])
        self.assertEqual(result["changes"]["BTC"], 0.017113)
        self.assertLess(result["changes"]["USD"], 0)  # Negative for buy
        self.assertIn("transaction_record", result)
        self.assertEqual(result["transaction_record"]["type"], "BUY")
        self.assertEqual(result["transaction_record"]["asset"], "BTC")
    
    @patch.object(CryptoOrderWorkflow, '_validate_order_params')
    @patch.object(CryptoOrderWorkflow, '_check_available_funds')
    @patch.object(CryptoOrderWorkflow, '_calculate_order_details')
    @patch.object(CryptoOrderWorkflow, '_submit_order')
    @patch.object(CryptoOrderWorkflow, '_monitor_order_status')
    @patch.object(CryptoOrderWorkflow, '_update_portfolio')
    def test_execute_all_steps(self, mock_update, mock_monitor, mock_submit, 
                              mock_calculate, mock_check, mock_validate):
        """Test executing all steps in the workflow"""
        # Setup mocks for all steps
        mock_validate.return_value = {"valid": True}
        mock_check.return_value = {"sufficient_funds": True}
        mock_calculate.return_value = {"amount_crypto": 0.017113}
        mock_submit.return_value = {"order_id": "test_order", "status": "FILLED"}
        mock_monitor.return_value = {"status": "FILLED", "filled_amount": 0.017113}
        mock_update.return_value = {"successful": True}
        
        workflow = CryptoOrderWorkflow(parameters=self.valid_parameters)
        results = workflow.execute_all_steps()
        
        # Check that all steps were executed
        self.assertEqual(len(results), 6)
        self.assertEqual(results[0]["status"], "success")
        self.assertEqual(results[1]["status"], "success")
        self.assertEqual(results[2]["status"], "success")
        self.assertEqual(results[3]["status"], "success")
        self.assertEqual(results[4]["status"], "success")
        self.assertEqual(results[5]["status"], "success")
        
        # Check that all mocks were called
        mock_validate.assert_called_once()
        mock_check.assert_called_once()
        mock_calculate.assert_called_once()
        mock_submit.assert_called_once()
        mock_monitor.assert_called_once()
        mock_update.assert_called_once()
        
        # Check workflow completed status
        self.assertTrue(workflow.is_completed())


if __name__ == '__main__':
    unittest.main() 