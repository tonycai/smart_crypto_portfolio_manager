"""
Portfolio Monitoring Workflow

This workflow handles the continuous monitoring of a cryptocurrency portfolio:
1. Fetch current market data for portfolio assets
2. Calculate portfolio performance metrics
3. Check for risk threshold crossings
4. Generate monitoring alerts if necessary
5. Update monitoring dashboards
"""
import logging
import uuid
from typing import Dict, Any, List

from src.agents.orchestration_agent import Workflow, WorkflowStep

logger = logging.getLogger(__name__)

def get_workflow(parameters: Dict[str, Any]) -> Workflow:
    """
    Create a portfolio monitoring workflow with the given parameters.
    This function is required by the orchestration agent to load the workflow.
    
    Args:
        parameters (dict): Workflow parameters including:
            - portfolio_id: ID of the portfolio to monitor
            - monitoring_interval: how often to check (in minutes)
            - risk_thresholds: dictionary of thresholds that trigger alerts
            - alert_recipients: list of recipients for alerts
            
    Returns:
        Workflow: A Workflow object with all steps defined
    """
    logger.info("Creating portfolio monitoring workflow")
    
    # Validate required parameters
    required_params = ["portfolio_id", "monitoring_interval"]
    for param in required_params:
        if param not in parameters:
            raise ValueError(f"Missing required parameter: {param}")
    
    # Set default values for optional parameters
    if "risk_thresholds" not in parameters:
        parameters["risk_thresholds"] = {
            "volatility_max": 0.05,
            "drawdown_max": 0.10,
            "value_change_pct": 0.07
        }
    
    if "alert_recipients" not in parameters:
        parameters["alert_recipients"] = ["default@example.com"]
    
    # Create workflow instance
    workflow_id = f"portfolio-monitor-{uuid.uuid4()}"
    workflow = Workflow(workflow_id, "Portfolio Monitoring", parameters)
    
    # Add workflow steps
    workflow.add_step("fetch_market_data", "market_data_agent")
    workflow.add_step("calculate_performance_metrics", "portfolio_agent")
    workflow.add_step("check_risk_thresholds", "risk_analysis_agent")
    workflow.add_step("generate_alerts", "notification_agent")
    workflow.add_step("update_dashboards", "reporting_agent")
    
    logger.info(f"Created portfolio monitoring workflow with ID {workflow_id}")
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
    
    # Get the step name from the context
    step_name = None
    for result in context.values():
        if isinstance(result, dict) and "step_name" in result and result.get("step_id") == step_id:
            step_name = result["step_name"]
            break
    
    # Default simulated results
    results = {
        "status": "completed",
        "step_id": step_id,
        "step_name": step_name
    }
    
    # Simulate specific step results based on step name
    if "fetch_market_data" in step_id:
        results["market_data"] = {
            "timestamp": "2023-05-15T14:30:00Z",
            "assets": {
                "BTC": {"price": 58432.15, "24h_change": 2.3, "volume": 28500000000},
                "ETH": {"price": 2834.67, "24h_change": 1.2, "volume": 14200000000},
                "SOL": {"price": 135.56, "24h_change": 4.7, "volume": 3800000000},
                "AVAX": {"price": 35.78, "24h_change": -1.8, "volume": 620000000},
                "ADA": {"price": 0.58, "24h_change": -0.5, "volume": 540000000},
                "USDT": {"price": 1.00, "24h_change": 0.01, "volume": 86500000000}
            },
            "market_indicators": {
                "crypto_fear_greed_index": 65,
                "btc_dominance": 46.2,
                "total_market_cap": 2430000000000
            }
        }
        
    elif "calculate_performance_metrics" in step_id:
        portfolio_id = step_params.get("portfolio_id", "default")
        
        results["performance_metrics"] = {
            "portfolio_id": portfolio_id,
            "timestamp": "2023-05-15T14:35:00Z",
            "total_value_usd": 29240.35,
            "24h_change_pct": 2.45,
            "7d_change_pct": 5.32,
            "30d_change_pct": 8.76,
            "allocation": {
                "BTC": 0.42,  # 42%
                "ETH": 0.25,  # 25%
                "SOL": 0.15,  # 15%
                "AVAX": 0.05,  # 5%
                "ADA": 0.03,  # 3%
                "USDT": 0.10   # 10%
            },
            "volatility": 0.042,
            "sharpe_ratio": 1.35,
            "drawdown": 0.064,
            "correlation_matrix": {
                "BTC_ETH": 0.82,
                "BTC_SOL": 0.71,
                "ETH_SOL": 0.78
            }
        }
        
    elif "check_risk_thresholds" in step_id:
        # Get performance metrics from previous step
        performance_metrics = {}
        risk_thresholds = step_params.get("risk_thresholds", {})
        
        if "calculate_performance_metrics" in context:
            performance_metrics = context["calculate_performance_metrics"].get("performance_metrics", {})
        
        # Check for threshold crossings
        threshold_alerts = []
        
        # Check volatility
        if "volatility" in performance_metrics and "volatility_max" in risk_thresholds:
            if performance_metrics["volatility"] > risk_thresholds["volatility_max"]:
                threshold_alerts.append({
                    "type": "VOLATILITY_HIGH",
                    "threshold": risk_thresholds["volatility_max"],
                    "value": performance_metrics["volatility"],
                    "message": f"Portfolio volatility ({performance_metrics['volatility']:.2%}) exceeds threshold ({risk_thresholds['volatility_max']:.2%})"
                })
        
        # Check drawdown
        if "drawdown" in performance_metrics and "drawdown_max" in risk_thresholds:
            if performance_metrics["drawdown"] > risk_thresholds["drawdown_max"]:
                threshold_alerts.append({
                    "type": "DRAWDOWN_HIGH",
                    "threshold": risk_thresholds["drawdown_max"],
                    "value": performance_metrics["drawdown"],
                    "message": f"Portfolio drawdown ({performance_metrics['drawdown']:.2%}) exceeds threshold ({risk_thresholds['drawdown_max']:.2%})"
                })
        
        # Check value change
        if "24h_change_pct" in performance_metrics and "value_change_pct" in risk_thresholds:
            change = abs(performance_metrics["24h_change_pct"] / 100)  # Convert percentage to decimal
            if change > risk_thresholds["value_change_pct"]:
                direction = "increase" if performance_metrics["24h_change_pct"] > 0 else "decrease"
                threshold_alerts.append({
                    "type": "VALUE_CHANGE_HIGH",
                    "threshold": risk_thresholds["value_change_pct"],
                    "value": change,
                    "message": f"Portfolio value {direction} ({performance_metrics['24h_change_pct']:.2f}%) exceeds threshold ({risk_thresholds['value_change_pct']:.2%})"
                })
        
        results["threshold_analysis"] = {
            "alerts_triggered": len(threshold_alerts) > 0,
            "num_alerts": len(threshold_alerts),
            "alerts": threshold_alerts,
            "risk_level": "HIGH" if len(threshold_alerts) > 1 else "MEDIUM" if len(threshold_alerts) == 1 else "LOW"
        }
        
    elif "generate_alerts" in step_id:
        # Get threshold analysis from previous step
        threshold_analysis = {}
        alert_recipients = step_params.get("alert_recipients", [])
        
        if "check_risk_thresholds" in context:
            threshold_analysis = context["check_risk_thresholds"].get("threshold_analysis", {})
        
        # Generate notifications if alerts were triggered
        notifications = []
        
        if threshold_analysis.get("alerts_triggered", False):
            alerts = threshold_analysis.get("alerts", [])
            risk_level = threshold_analysis.get("risk_level", "LOW")
            
            for recipient in alert_recipients:
                notifications.append({
                    "recipient": recipient,
                    "subject": f"Portfolio Alert: {risk_level} Risk Level Detected",
                    "body": f"Your portfolio has triggered {len(alerts)} alert(s):\n" + 
                            "\n".join([alert["message"] for alert in alerts]),
                    "timestamp": "2023-05-15T14:40:00Z",
                    "delivery_status": "PENDING"
                })
        
        results["notifications"] = {
            "sent": len(notifications) > 0,
            "count": len(notifications),
            "details": notifications
        }
        
    elif "update_dashboards" in step_id:
        # Get data from previous steps to update dashboards
        portfolio_id = step_params.get("portfolio_id", "default")
        market_data = {}
        performance_metrics = {}
        threshold_analysis = {}
        
        if "fetch_market_data" in context:
            market_data = context["fetch_market_data"].get("market_data", {})
        
        if "calculate_performance_metrics" in context:
            performance_metrics = context["calculate_performance_metrics"].get("performance_metrics", {})
            
        if "check_risk_thresholds" in context:
            threshold_analysis = context["check_risk_thresholds"].get("threshold_analysis", {})
        
        # Simulate dashboard update
        dashboard_updates = {
            "portfolio_overview": {
                "last_updated": "2023-05-15T14:45:00Z",
                "data_updated": True,
                "components_updated": ["value_chart", "allocation_pie", "performance_metrics", "risk_indicators"]
            },
            "risk_dashboard": {
                "last_updated": "2023-05-15T14:45:00Z",
                "data_updated": True,
                "alert_status_updated": threshold_analysis.get("alerts_triggered", False),
                "components_updated": ["risk_threshold_chart", "volatility_trend", "drawdown_indicator"]
            },
            "market_dashboard": {
                "last_updated": "2023-05-15T14:45:00Z",
                "data_updated": True,
                "components_updated": ["price_charts", "market_indicators", "correlation_heatmap"]
            }
        }
        
        results["dashboard_updates"] = dashboard_updates
    
    logger.info(f"Simulated execution of step: {step_id} completed")
    return results 