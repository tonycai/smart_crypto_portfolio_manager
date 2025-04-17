"""
Workflows package for the crypto portfolio management system.
Contains portfolio optimization and management workflows.
"""
# Import workflow modules
from src.workflows import portfolio_optimization
from src.workflows import market_analysis_workflow
from src.workflows import portfolio_rebalance_workflow

# Define the workflows available in this package
__all__ = [
    "portfolio_optimization",
    "market_analysis_workflow",
    "portfolio_rebalance_workflow"
] 