"""
Workflows Package

This package contains all the workflow definitions for the smart crypto portfolio manager.
"""

from src.workflows.base_workflow import BaseWorkflow, WorkflowStep, StepStatus
from enum import Enum

__all__ = ["BaseWorkflow", "WorkflowStep", "StepStatus"]

class WorkflowStatus(str, Enum):
    """Status states for workflows"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED" 