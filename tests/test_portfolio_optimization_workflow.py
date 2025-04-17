import unittest
from unittest.mock import patch, MagicMock
import json

from src.workflows.portfolio_optimization_workflow import PortfolioOptimizationWorkflow
from src.workflows.base_workflow import StepStatus

class TestPortfolioOptimizationWorkflow(unittest.TestCase):
    """Test cases for the PortfolioOptimizationWorkflow class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.valid_params = {
            'risk_tolerance': 5,
            'investment_amount': 10000,
            'investment_horizon': 365
        }
        self.workflow = PortfolioOptimizationWorkflow(params=self.valid_params)
    
    def test_initialization(self):
        """Test if the workflow initializes correctly."""
        self.assertEqual(self.workflow.name, "Portfolio Optimization")
        self.assertEqual(self.workflow.params, self.valid_params)
        self.assertEqual(len(self.workflow.steps), 5)
        
        # Check if all steps are defined
        expected_steps = [
            "collect_market_data",
            "analyze_risk_profile",
            "generate_optimization_models",
            "run_optimization",
            "generate_recommendations"
        ]
        actual_steps = [step.name for step in self.workflow.steps]
        self.assertEqual(actual_steps, expected_steps)
    
    def test_validate_parameters_valid(self):
        """Test parameter validation with valid parameters."""
        self.assertTrue(self.workflow.validate_parameters())
    
    def test_validate_parameters_invalid_risk_tolerance(self):
        """Test parameter validation with invalid risk tolerance."""
        # Test with risk_tolerance outside valid range
        workflow = PortfolioOptimizationWorkflow(params={
            'risk_tolerance': 11,  # Invalid: > 10
            'investment_amount': 10000,
            'investment_horizon': 365
        })
        self.assertFalse(workflow.validate_parameters())
        
        # Test with negative risk_tolerance
        workflow = PortfolioOptimizationWorkflow(params={
            'risk_tolerance': -1,  # Invalid: < 1
            'investment_amount': 10000,
            'investment_horizon': 365
        })
        self.assertFalse(workflow.validate_parameters())
    
    def test_validate_parameters_invalid_investment_amount(self):
        """Test parameter validation with invalid investment amount."""
        # Test with negative investment amount
        workflow = PortfolioOptimizationWorkflow(params={
            'risk_tolerance': 5,
            'investment_amount': -100,  # Invalid: negative
            'investment_horizon': 365
        })
        self.assertFalse(workflow.validate_parameters())
        
        # Test with zero investment amount
        workflow = PortfolioOptimizationWorkflow(params={
            'risk_tolerance': 5,
            'investment_amount': 0,  # Invalid: zero
            'investment_horizon': 365
        })
        self.assertFalse(workflow.validate_parameters())
    
    def test_validate_parameters_invalid_investment_horizon(self):
        """Test parameter validation with invalid investment horizon."""
        # Test with negative investment horizon
        workflow = PortfolioOptimizationWorkflow(params={
            'risk_tolerance': 5,
            'investment_amount': 10000,
            'investment_horizon': -10  # Invalid: negative
        })
        self.assertFalse(workflow.validate_parameters())
        
        # Test with zero investment horizon
        workflow = PortfolioOptimizationWorkflow(params={
            'risk_tolerance': 5,
            'investment_amount': 10000,
            'investment_horizon': 0  # Invalid: zero
        })
        self.assertFalse(workflow.validate_parameters())
    
    def test_validate_parameters_missing(self):
        """Test parameter validation with missing parameters."""
        # Missing risk_tolerance
        workflow = PortfolioOptimizationWorkflow(params={
            'investment_amount': 10000,
            'investment_horizon': 365
        })
        self.assertFalse(workflow.validate_parameters())
        
        # Missing investment_amount
        workflow = PortfolioOptimizationWorkflow(params={
            'risk_tolerance': 5,
            'investment_horizon': 365
        })
        self.assertFalse(workflow.validate_parameters())
        
        # Missing investment_horizon
        workflow = PortfolioOptimizationWorkflow(params={
            'risk_tolerance': 5,
            'investment_amount': 10000
        })
        self.assertFalse(workflow.validate_parameters())
    
    def test_collect_market_data(self):
        """Test the market data collection step."""
        result = self.workflow.collect_market_data()
        
        self.assertEqual(result["status"], "success")
        self.assertIn("data", result)
        self.assertIn("currencies", result["data"])
        
        # Verify we have at least some currencies
        self.assertGreaterEqual(len(result["data"]["currencies"]), 1)
    
    def test_analyze_risk_profile(self):
        """Test the risk profile analysis step."""
        result = self.workflow.analyze_risk_profile()
        
        self.assertEqual(result["status"], "success")
        self.assertIn("data", result)
        
        # Check if risk profile data is generated
        risk_data = result["data"]
        self.assertIn("risk_profile", risk_data)
        self.assertIn("volatility_target", risk_data)
        self.assertIn("max_allocation", risk_data)
        
        # For risk_tolerance 5, should be "moderate" profile
        self.assertEqual(risk_data["risk_profile"], "moderate")
    
    def test_analyze_risk_profile_conservative(self):
        """Test risk profile analysis with conservative settings."""
        workflow = PortfolioOptimizationWorkflow(params={
            'risk_tolerance': 2,
            'investment_amount': 10000,
            'investment_horizon': 365
        })
        
        result = workflow.analyze_risk_profile()
        self.assertEqual(result["data"]["risk_profile"], "conservative")
        self.assertEqual(result["data"]["volatility_target"], "low")
        self.assertLess(result["data"]["max_allocation"], 0.2)  # Should be lower than moderate
    
    def test_analyze_risk_profile_aggressive(self):
        """Test risk profile analysis with aggressive settings."""
        workflow = PortfolioOptimizationWorkflow(params={
            'risk_tolerance': 9,
            'investment_amount': 10000,
            'investment_horizon': 365
        })
        
        result = workflow.analyze_risk_profile()
        self.assertEqual(result["data"]["risk_profile"], "aggressive")
        self.assertEqual(result["data"]["volatility_target"], "high")
        self.assertGreater(result["data"]["max_allocation"], 0.3)  # Should be higher than moderate
    
    @patch('src.workflows.portfolio_optimization_workflow.PortfolioOptimizationWorkflow.get_step')
    def test_generate_optimization_models(self, mock_get_step):
        """Test the generation of optimization models."""
        # Mock the prerequisite steps
        market_data_step = MagicMock()
        market_data_step.status = StepStatus.COMPLETED
        market_data_step.result = {
            "data": {
                "currencies": [
                    {"symbol": "BTC", "price": 65000, "24h_change": 2.5, "market_cap": 1200000000000},
                    {"symbol": "ETH", "price": 3500, "24h_change": 3.1, "market_cap": 400000000000}
                ]
            }
        }
        
        risk_profile_step = MagicMock()
        risk_profile_step.status = StepStatus.COMPLETED
        risk_profile_step.result = {
            "data": {
                "risk_profile": "moderate",
                "volatility_target": "medium",
                "max_allocation": 0.25,
                "risk_tolerance_score": 5
            }
        }
        
        # Set up the mock to return our mocked steps
        mock_get_step.side_effect = lambda step_name: {
            "collect_market_data": market_data_step,
            "analyze_risk_profile": risk_profile_step
        }.get(step_name)
        
        # Run the method
        result = self.workflow.generate_optimization_models()
        
        # Verify the result
        self.assertEqual(result["status"], "success")
        self.assertIn("models", result["data"])
        self.assertGreaterEqual(len(result["data"]["models"]), 1)
        
        # Check if models contain expected parameters
        for model in result["data"]["models"]:
            self.assertIn("name", model)
            self.assertIn("parameters", model)
    
    @patch('src.workflows.portfolio_optimization_workflow.PortfolioOptimizationWorkflow.get_step')
    def test_run_optimization(self, mock_get_step):
        """Test running the optimization algorithms."""
        # Mock the prerequisite step
        models_step = MagicMock()
        models_step.status = StepStatus.COMPLETED
        models_step.result = {
            "data": {
                "models": [
                    {
                        "name": "Mean-Variance",
                        "parameters": {"risk_aversion": 5}
                    },
                    {
                        "name": "Risk Parity",
                        "parameters": {"target_volatility": "medium"}
                    }
                ]
            }
        }
        
        # Set up the mock to return our mocked step
        mock_get_step.return_value = models_step
        
        # Run the method
        result = self.workflow.run_optimization()
        
        # Verify the result
        self.assertEqual(result["status"], "success")
        self.assertIn("optimized_portfolios", result["data"])
        self.assertGreaterEqual(len(result["data"]["optimized_portfolios"]), 1)
        
        # Check if portfolios contain the expected properties
        for portfolio in result["data"]["optimized_portfolios"]:
            self.assertIn("model", portfolio)
            self.assertIn("expected_return", portfolio)
            self.assertIn("expected_volatility", portfolio)
            self.assertIn("allocations", portfolio)
            
            # Check if allocations sum to approximately 1.0 (100%)
            total_allocation = sum(alloc["weight"] for alloc in portfolio["allocations"])
            self.assertAlmostEqual(total_allocation, 1.0, places=2)
    
    @patch('src.workflows.portfolio_optimization_workflow.PortfolioOptimizationWorkflow.get_step')
    def test_generate_recommendations(self, mock_get_step):
        """Test generating portfolio recommendations."""
        # Mock the optimization step
        optimization_step = MagicMock()
        optimization_step.status = StepStatus.COMPLETED
        optimization_step.result = {
            "data": {
                "optimized_portfolios": [
                    {
                        "model": "Mean-Variance",
                        "expected_return": 0.15,
                        "expected_volatility": 0.25,
                        "sharpe_ratio": 0.6,
                        "allocations": [
                            {"symbol": "BTC", "weight": 0.35},
                            {"symbol": "ETH", "weight": 0.25},
                            {"symbol": "SOL", "weight": 0.15},
                            {"symbol": "ADA", "weight": 0.10},
                            {"symbol": "DOT", "weight": 0.10},
                            {"symbol": "LINK", "weight": 0.05}
                        ]
                    },
                    {
                        "model": "Risk Parity",
                        "expected_return": 0.12,
                        "expected_volatility": 0.18,
                        "sharpe_ratio": 0.67,
                        "allocations": [
                            {"symbol": "BTC", "weight": 0.25},
                            {"symbol": "ETH", "weight": 0.20},
                            {"symbol": "SOL", "weight": 0.15},
                            {"symbol": "ADA", "weight": 0.15},
                            {"symbol": "DOT", "weight": 0.15},
                            {"symbol": "LINK", "weight": 0.10}
                        ]
                    }
                ]
            }
        }
        
        # Mock the risk profile step
        risk_profile_step = MagicMock()
        risk_profile_step.status = StepStatus.COMPLETED
        risk_profile_step.result = {
            "data": {
                "risk_profile": "moderate",
                "volatility_target": "medium",
                "max_allocation": 0.25,
                "risk_tolerance_score": 5
            }
        }
        
        # Set up the mock to return our mocked steps
        mock_get_step.side_effect = lambda step_name: {
            "run_optimization": optimization_step,
            "analyze_risk_profile": risk_profile_step
        }.get(step_name)
        
        # Run the method
        result = self.workflow.generate_recommendations()
        
        # Verify the result
        self.assertEqual(result["status"], "success")
        self.assertIn("data", result)
        
        recommendation_data = result["data"]
        self.assertIn("portfolio_name", recommendation_data)
        self.assertIn("expected_annual_return", recommendation_data)
        self.assertIn("expected_annual_volatility", recommendation_data)
        self.assertIn("allocations", recommendation_data)
        
        # For moderate risk profile, should select portfolio with highest Sharpe ratio
        self.assertEqual(recommendation_data["model_used"], "Risk Parity")  # The one with higher Sharpe
        
        # Check allocations sum to 100%
        total_percentage = sum(alloc["percentage"] for alloc in recommendation_data["allocations"])
        self.assertAlmostEqual(total_percentage, 100, places=1)
        
        # Check if amounts sum to investment_amount
        total_amount = sum(alloc["amount"] for alloc in recommendation_data["allocations"])
        self.assertAlmostEqual(total_amount, 10000, places=2)
    
    def test_execute_workflow(self):
        """Test executing the entire workflow."""
        # Execute the workflow
        result = self.workflow.execute()
        
        # Verify workflow completed successfully
        self.assertTrue(result)
        
        # Check if all steps were completed
        for step in self.workflow.steps:
            self.assertEqual(step.status, StepStatus.COMPLETED)
        
        # Verify the final recommendation has all required fields
        recommendations = self.workflow.get_step("generate_recommendations").result["data"]
        self.assertIn("portfolio_name", recommendations)
        self.assertIn("allocations", recommendations)
        self.assertIn("expected_annual_return", recommendations)
        self.assertIn("investment_amount", recommendations)

if __name__ == '__main__':
    unittest.main() 