"""
Crypto Order Workflow

This workflow handles the process of placing and managing crypto orders:
1. Validate order parameters
2. Check available funds
3. Calculate order size, price, and fees
4. Submit the order to the exchange
5. Monitor order status until completion
6. Update portfolio with the executed order
"""
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.agents.orchestration_agent import Workflow, WorkflowStep
from src.workflows.base_workflow import BaseWorkflow, StepStatus

logger = logging.getLogger(__name__)

# Legacy approach (compatible with orchestration_agent.py)
def get_workflow(parameters: Dict[str, Any]) -> Workflow:
    """
    Create a crypto order workflow with the given parameters.
    This function is required by the orchestration agent to load the workflow.
    
    Args:
        parameters (dict): Workflow parameters including:
            - asset: Symbol of the cryptocurrency (e.g., "BTC")
            - order_type: Type of order (MARKET, LIMIT)
            - side: Buy or sell
            - amount: Amount to buy/sell (in USD or crypto)
            - is_amount_in_usd: Whether the amount is in USD (True) or crypto units (False)
            - price: Price for limit orders (ignored for market orders)
            - portfolio_id: ID of the portfolio to update
            
    Returns:
        Workflow: A Workflow object with all steps defined
    """
    logger.info("Creating crypto order workflow")
    
    # Validate required parameters
    required_params = ["asset", "order_type", "side", "amount", "portfolio_id"]
    for param in required_params:
        if param not in parameters:
            raise ValueError(f"Missing required parameter: {param}")
    
    # Validate order_type
    valid_order_types = ["MARKET", "LIMIT"]
    if parameters["order_type"] not in valid_order_types:
        raise ValueError(f"Invalid order_type. Must be one of: {valid_order_types}")
    
    # Validate side
    valid_sides = ["BUY", "SELL"]
    if parameters["side"] not in valid_sides:
        raise ValueError(f"Invalid side. Must be one of: {valid_sides}")
    
    # Validate amount
    try:
        amount = float(parameters["amount"])
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
    except (ValueError, TypeError):
        raise ValueError("Amount must be a positive number")
    
    # Set default values for optional parameters
    if "is_amount_in_usd" not in parameters:
        parameters["is_amount_in_usd"] = True
    
    # For LIMIT orders, price is required
    if parameters["order_type"] == "LIMIT" and "price" not in parameters:
        raise ValueError("Price is required for LIMIT orders")
    
    # Create workflow instance
    workflow_id = f"crypto-order-{uuid.uuid4()}"
    workflow = Workflow(workflow_id, "Crypto Order", parameters)
    
    # Add workflow steps
    workflow.add_step("validate_order_params", "validation_agent")
    workflow.add_step("check_available_funds", "portfolio_agent")
    workflow.add_step("calculate_order_details", "order_calculation_agent")
    workflow.add_step("submit_order", "exchange_agent")
    workflow.add_step("monitor_order_status", "exchange_agent")
    workflow.add_step("update_portfolio", "portfolio_agent")
    
    logger.info(f"Created crypto order workflow with ID {workflow_id}")
    return workflow

def simulate_step_execution(step_id: str, step_params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate execution of a workflow step for demonstration purposes.
    
    Args:
        step_id (str): The ID of the step being executed
        step_params (dict): Parameters for the step
        context (dict): Execution context including results from previous steps
        
    Returns:
        dict: Simulated results for the step
    """
    logger.info(f"Simulating execution of step: {step_id}")
    
    # Default simulated results
    results = {
        "status": "completed",
        "step_id": step_id,
        "timestamp": datetime.now().isoformat()
    }
    
    # Simulate specific step results based on step name
    if "validate_order_params" in step_id:
        asset = step_params.get("asset", "BTC")
        order_type = step_params.get("order_type", "MARKET")
        side = step_params.get("side", "BUY")
        
        results["validation_result"] = {
            "valid": True,
            "asset_exists": True,
            "asset_active": True,
            "trading_enabled": True,
            "min_order_size": {
                "BTC": 0.0001,
                "ETH": 0.01,
                "SOL": 0.1
            }.get(asset, 1.0),
            "max_leverage": 3.0 if asset in ["BTC", "ETH"] else 2.0,
            "warnings": []
        }
        
    elif "check_available_funds" in step_id:
        portfolio_id = step_params.get("portfolio_id", "default")
        asset = step_params.get("asset", "BTC")
        side = step_params.get("side", "BUY")
        
        results["funds_check"] = {
            "portfolio_id": portfolio_id,
            "sufficient_funds": True,
            "available_usd": 25000.50,
            "available_crypto": {
                "BTC": 0.5,
                "ETH": 5.0,
                "SOL": 50.0,
                "USDT": 10000.0
            },
            "max_order_size_usd": 20000.0 if side == "BUY" else None,
            "max_order_size_crypto": None if side == "BUY" else {
                "BTC": 0.5,
                "ETH": 5.0,
                "SOL": 50.0
            }.get(asset, 0.0)
        }
        
    elif "calculate_order_details" in step_id:
        asset = step_params.get("asset", "BTC")
        order_type = step_params.get("order_type", "MARKET")
        side = step_params.get("side", "BUY")
        amount = float(step_params.get("amount", 1000))
        is_amount_in_usd = step_params.get("is_amount_in_usd", True)
        price = step_params.get("price")
        
        # Simulate current market prices
        market_prices = {
            "BTC": 58432.15,
            "ETH": 2834.67,
            "SOL": 135.56
        }
        current_price = market_prices.get(asset, 100.0)
        
        # Calculate order size
        if is_amount_in_usd:
            crypto_amount = amount / current_price
        else:
            crypto_amount = amount
            amount = crypto_amount * current_price
        
        # Calculate fees (0.1% fee)
        fee_rate = 0.001
        fee_usd = amount * fee_rate
        
        results["order_details"] = {
            "asset": asset,
            "order_type": order_type,
            "side": side,
            "price": price if order_type == "LIMIT" else current_price,
            "amount_usd": amount,
            "amount_crypto": crypto_amount,
            "estimated_fee_usd": fee_usd,
            "estimated_fee_crypto": fee_usd / current_price,
            "total_cost_usd": amount + fee_usd if side == "BUY" else amount - fee_usd,
            "market_price": current_price,
            "market_24h_change": 2.3 if asset == "BTC" else 1.2 if asset == "ETH" else 4.7,
            "timestamp": datetime.now().isoformat()
        }
        
    elif "submit_order" in step_id:
        # Get order details from previous step
        order_details = {}
        if "calculate_order_details" in context:
            order_details = context["calculate_order_details"].get("order_details", {})
        
        asset = order_details.get("asset", step_params.get("asset", "BTC"))
        order_type = order_details.get("order_type", step_params.get("order_type", "MARKET"))
        side = order_details.get("side", step_params.get("side", "BUY"))
        price = order_details.get("price", step_params.get("price"))
        amount_crypto = order_details.get("amount_crypto", 0.1)
        
        # Simulate order submission
        order_id = f"ord_{uuid.uuid4().hex[:12]}"
        
        results["order_submission"] = {
            "success": True,
            "order_id": order_id,
            "exchange": "binance",
            "asset": asset,
            "order_type": order_type,
            "side": side,
            "price": price,
            "size": amount_crypto,
            "status": "OPEN" if order_type == "LIMIT" else "FILLED",
            "filled_amount": 0.0 if order_type == "LIMIT" else amount_crypto,
            "remaining_amount": amount_crypto if order_type == "LIMIT" else 0.0,
            "timestamp": datetime.now().isoformat(),
            "estimated_completion_time": None if order_type == "MARKET" else (
                datetime.now().isoformat() if order_type == "LIMIT" and price == order_details.get("market_price") 
                else None
            )
        }
        
    elif "monitor_order_status" in step_id:
        # Get order submission from previous step
        order_submission = {}
        if "submit_order" in context:
            order_submission = context["submit_order"].get("order_submission", {})
        
        order_id = order_submission.get("order_id", f"ord_{uuid.uuid4().hex[:12]}")
        order_type = order_submission.get("order_type", "MARKET")
        
        # For market orders, they are already filled
        if order_type == "MARKET":
            status = "FILLED"
            filled_amount = order_submission.get("size", 0.1)
            remaining_amount = 0.0
        else:
            # For limit orders, simulate a partial fill
            status = "PARTIALLY_FILLED"
            filled_amount = order_submission.get("size", 0.1) * 0.7  # 70% filled
            remaining_amount = order_submission.get("size", 0.1) * 0.3  # 30% remaining
        
        results["order_status"] = {
            "order_id": order_id,
            "status": status,
            "filled_amount": filled_amount,
            "remaining_amount": remaining_amount,
            "fill_price": order_submission.get("price", 58000),
            "transaction_ids": [f"tx_{uuid.uuid4().hex[:8]}" for _ in range(3)],
            "last_update": datetime.now().isoformat(),
            "time_in_force": "GTC" if order_type == "LIMIT" else None,
            "is_cancelable": status != "FILLED"
        }
        
    elif "update_portfolio" in step_id:
        # Get order status from previous step
        order_status = {}
        if "monitor_order_status" in context:
            order_status = context["monitor_order_status"].get("order_status", {})
            
        # Get order details
        order_details = {}
        if "calculate_order_details" in context:
            order_details = context["calculate_order_details"].get("order_details", {})
            
        portfolio_id = step_params.get("portfolio_id", "default")
        asset = order_details.get("asset", "BTC")
        side = order_details.get("side", "BUY")
        filled_amount = order_status.get("filled_amount", 0.1)
        fill_price = order_status.get("fill_price", 58000)
        
        # Calculate USD value
        usd_value = filled_amount * fill_price
        
        # Calculate updated portfolio balances
        if side == "BUY":
            usd_change = -usd_value
            crypto_change = filled_amount
        else:  # SELL
            usd_change = usd_value
            crypto_change = -filled_amount
            
        results["portfolio_update"] = {
            "portfolio_id": portfolio_id,
            "successful": True,
            "timestamp": datetime.now().isoformat(),
            "changes": {
                "USD": usd_change,
                asset: crypto_change
            },
            "new_balances": {
                "USD": 25000.50 + usd_change,
                "BTC": 0.5 + (crypto_change if asset == "BTC" else 0),
                "ETH": 5.0 + (crypto_change if asset == "ETH" else 0),
                "SOL": 50.0 + (crypto_change if asset == "SOL" else 0),
                "USDT": 10000.0
            },
            "transaction_record": {
                "tx_id": f"ptx_{uuid.uuid4().hex[:8]}",
                "type": side,
                "asset": asset,
                "amount": filled_amount,
                "price": fill_price,
                "value_usd": usd_value,
                "fee_usd": usd_value * 0.001,
                "timestamp": datetime.now().isoformat(),
                "exchange": "binance",
                "order_id": order_status.get("order_id")
            }
        }
    
    logger.info(f"Simulated execution of step: {step_id} completed")
    return results

# Modern OOP approach (using BaseWorkflow)
class CryptoOrderWorkflow(BaseWorkflow):
    """
    A workflow for placing and managing crypto orders.
    
    This workflow orchestrates the following steps:
    1. Validate order parameters
    2. Check available funds
    3. Calculate order size, price, and fees
    4. Submit the order to the exchange
    5. Monitor order status until completion
    6. Update portfolio with the executed order
    """
    
    def __init__(
        self,
        workflow_id: str = None,
        parameters: Dict[str, Any] = None
    ):
        """
        Initialize a crypto order workflow
        
        Args:
            workflow_id: Optional workflow ID
            parameters: Workflow parameters including:
                - asset: Symbol of the cryptocurrency (e.g., "BTC")
                - order_type: Type of order (MARKET, LIMIT)
                - side: Buy or sell
                - amount: Amount to buy/sell (in USD or crypto)
                - is_amount_in_usd: Whether the amount is in USD (True) or crypto units (False)
                - price: Price for limit orders (ignored for market orders)
                - portfolio_id: ID of the portfolio to update
        """
        super().__init__(
            name="Crypto Order",
            description="Place and manage cryptocurrency orders",
            parameters=parameters or {}
        )
        
        if workflow_id:
            self.id = workflow_id
    
    def define_steps(self) -> None:
        """Define the workflow steps"""
        self.add_step(
            name="Validate Order Parameters",
            function=self._validate_order_params,
            description="Validate the order parameters and check if trading is available"
        )
        
        self.add_step(
            name="Check Available Funds",
            function=self._check_available_funds,
            description="Check if sufficient funds are available for the order"
        )
        
        self.add_step(
            name="Calculate Order Details",
            function=self._calculate_order_details,
            description="Calculate order size, price, and fees"
        )
        
        self.add_step(
            name="Submit Order",
            function=self._submit_order,
            description="Submit the order to the exchange"
        )
        
        self.add_step(
            name="Monitor Order Status",
            function=self._monitor_order_status,
            description="Monitor the order status until completion"
        )
        
        self.add_step(
            name="Update Portfolio",
            function=self._update_portfolio,
            description="Update the portfolio with the executed order"
        )
    
    def validate_parameters(self) -> bool:
        """
        Validate that all required parameters for the workflow are present and valid.
        
        Returns:
            True if all parameters are valid, False otherwise
        """
        required_params = ["asset", "order_type", "side", "amount", "portfolio_id"]
        for param in required_params:
            if param not in self.parameters:
                logger.error(f"Missing required parameter: {param}")
                return False
        
        # Validate order_type
        valid_order_types = ["MARKET", "LIMIT"]
        if self.parameters["order_type"] not in valid_order_types:
            logger.error(f"Invalid order_type. Must be one of: {valid_order_types}")
            return False
        
        # Validate side
        valid_sides = ["BUY", "SELL"]
        if self.parameters["side"] not in valid_sides:
            logger.error(f"Invalid side. Must be one of: {valid_sides}")
            return False
        
        # Validate amount
        try:
            amount = float(self.parameters["amount"])
            if amount <= 0:
                logger.error("Amount must be greater than zero")
                return False
        except (ValueError, TypeError):
            logger.error("Amount must be a positive number")
            return False
        
        # For LIMIT orders, price is required
        if self.parameters["order_type"] == "LIMIT" and "price" not in self.parameters:
            logger.error("Price is required for LIMIT orders")
            return False
        
        return True
    
    def _validate_order_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the order parameters and check if trading is available.
        
        Args:
            params: Workflow parameters
            
        Returns:
            Validation results
        """
        logger.info(f"Validating order parameters for {params['asset']}")
        
        # Simulate validation logic
        return {
            "valid": True,
            "asset_exists": True,
            "asset_active": True,
            "trading_enabled": True,
            "min_order_size": {
                "BTC": 0.0001,
                "ETH": 0.01,
                "SOL": 0.1
            }.get(params["asset"], 1.0),
            "max_leverage": 3.0 if params["asset"] in ["BTC", "ETH"] else 2.0,
            "warnings": []
        }
    
    def _check_available_funds(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if sufficient funds are available for the order.
        
        Args:
            params: Workflow parameters
            
        Returns:
            Funds check results
        """
        logger.info(f"Checking available funds for {params['side']} order of {params['asset']}")
        
        # Simulate funds check logic
        return {
            "portfolio_id": params["portfolio_id"],
            "sufficient_funds": True,
            "available_usd": 25000.50,
            "available_crypto": {
                "BTC": 0.5,
                "ETH": 5.0,
                "SOL": 50.0,
                "USDT": 10000.0
            },
            "max_order_size_usd": 20000.0 if params["side"] == "BUY" else None,
            "max_order_size_crypto": None if params["side"] == "BUY" else {
                "BTC": 0.5,
                "ETH": 5.0,
                "SOL": 50.0
            }.get(params["asset"], 0.0)
        }
    
    def _calculate_order_details(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate order size, price, and fees.
        
        Args:
            params: Workflow parameters
            
        Returns:
            Order details
        """
        logger.info(f"Calculating order details for {params['side']} {params['asset']}")
        
        # Simulate current market prices
        market_prices = {
            "BTC": 58432.15,
            "ETH": 2834.67,
            "SOL": 135.56
        }
        current_price = market_prices.get(params["asset"], 100.0)
        
        # Get amount and check if it's in USD or crypto
        amount = float(params["amount"])
        is_amount_in_usd = params.get("is_amount_in_usd", True)
        
        # Calculate order size
        if is_amount_in_usd:
            crypto_amount = amount / current_price
        else:
            crypto_amount = amount
            amount = crypto_amount * current_price
        
        # Calculate fees (0.1% fee)
        fee_rate = 0.001
        fee_usd = amount * fee_rate
        
        return {
            "asset": params["asset"],
            "order_type": params["order_type"],
            "side": params["side"],
            "price": params.get("price") if params["order_type"] == "LIMIT" else current_price,
            "amount_usd": amount,
            "amount_crypto": crypto_amount,
            "estimated_fee_usd": fee_usd,
            "estimated_fee_crypto": fee_usd / current_price,
            "total_cost_usd": amount + fee_usd if params["side"] == "BUY" else amount - fee_usd,
            "market_price": current_price,
            "market_24h_change": 2.3 if params["asset"] == "BTC" else 1.2 if params["asset"] == "ETH" else 4.7,
            "timestamp": datetime.now().isoformat()
        }
    
    def _submit_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit the order to the exchange.
        
        Args:
            params: Workflow parameters
            
        Returns:
            Order submission results
        """
        logger.info(f"Submitting {params['order_type']} {params['side']} order for {params['asset']}")
        
        # Get order details from previous step
        order_details = self.steps[2].result
        
        # Simulate order submission
        order_id = f"ord_{uuid.uuid4().hex[:12]}"
        
        return {
            "success": True,
            "order_id": order_id,
            "exchange": "binance",
            "asset": params["asset"],
            "order_type": params["order_type"],
            "side": params["side"],
            "price": order_details["price"],
            "size": order_details["amount_crypto"],
            "status": "OPEN" if params["order_type"] == "LIMIT" else "FILLED",
            "filled_amount": 0.0 if params["order_type"] == "LIMIT" else order_details["amount_crypto"],
            "remaining_amount": order_details["amount_crypto"] if params["order_type"] == "LIMIT" else 0.0,
            "timestamp": datetime.now().isoformat(),
            "estimated_completion_time": None if params["order_type"] == "MARKET" else (
                datetime.now().isoformat() if params["order_type"] == "LIMIT" and 
                params.get("price") == order_details.get("market_price") else None
            )
        }
    
    def _monitor_order_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Monitor the order status until completion.
        
        Args:
            params: Workflow parameters
            
        Returns:
            Order status results
        """
        logger.info("Monitoring order status")
        
        # Get order submission from previous step
        order_submission = self.steps[3].result
        order_id = order_submission["order_id"]
        order_type = params["order_type"]
        
        # For market orders, they are already filled
        if order_type == "MARKET":
            status = "FILLED"
            filled_amount = order_submission["size"]
            remaining_amount = 0.0
        else:
            # For limit orders, simulate a partial fill
            status = "PARTIALLY_FILLED"
            filled_amount = order_submission["size"] * 0.7  # 70% filled
            remaining_amount = order_submission["size"] * 0.3  # 30% remaining
        
        return {
            "order_id": order_id,
            "status": status,
            "filled_amount": filled_amount,
            "remaining_amount": remaining_amount,
            "fill_price": order_submission["price"],
            "transaction_ids": [f"tx_{uuid.uuid4().hex[:8]}" for _ in range(3)],
            "last_update": datetime.now().isoformat(),
            "time_in_force": "GTC" if order_type == "LIMIT" else None,
            "is_cancelable": status != "FILLED"
        }
    
    def _update_portfolio(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the portfolio with the executed order.
        
        Args:
            params: Workflow parameters
            
        Returns:
            Portfolio update results
        """
        logger.info(f"Updating portfolio {params['portfolio_id']} with order results")
        
        # Get order status from previous step
        order_status = self.steps[4].result
        
        # Get order details
        order_details = self.steps[2].result
        
        # Calculate USD value
        filled_amount = order_status["filled_amount"]
        fill_price = order_status["fill_price"]
        usd_value = filled_amount * fill_price
        
        # Calculate updated portfolio balances
        if params["side"] == "BUY":
            usd_change = -usd_value
            crypto_change = filled_amount
        else:  # SELL
            usd_change = usd_value
            crypto_change = -filled_amount
            
        return {
            "portfolio_id": params["portfolio_id"],
            "successful": True,
            "timestamp": datetime.now().isoformat(),
            "changes": {
                "USD": usd_change,
                params["asset"]: crypto_change
            },
            "new_balances": {
                "USD": 25000.50 + usd_change,
                "BTC": 0.5 + (crypto_change if params["asset"] == "BTC" else 0),
                "ETH": 5.0 + (crypto_change if params["asset"] == "ETH" else 0),
                "SOL": 50.0 + (crypto_change if params["asset"] == "SOL" else 0),
                "USDT": 10000.0
            },
            "transaction_record": {
                "tx_id": f"ptx_{uuid.uuid4().hex[:8]}",
                "type": params["side"],
                "asset": params["asset"],
                "amount": filled_amount,
                "price": fill_price,
                "value_usd": usd_value,
                "fee_usd": usd_value * 0.001,
                "timestamp": datetime.now().isoformat(),
                "exchange": "binance",
                "order_id": order_status["order_id"]
            }
        }

def create_crypto_order_workflow(parameters: Dict[str, Any]) -> CryptoOrderWorkflow:
    """
    Helper function to create a crypto order workflow
    
    Args:
        parameters: Workflow parameters
        
    Returns:
        A configured crypto order workflow
    """
    try:
        workflow = CryptoOrderWorkflow(parameters=parameters)
        logger.info(f"Created crypto order workflow: {workflow.id}")
        return workflow
    except Exception as e:
        logger.error(f"Failed to create crypto order workflow: {str(e)}")
        raise 