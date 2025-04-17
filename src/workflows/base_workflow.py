"""
Base Workflow Module

This module defines the base classes for all workflows in the system.
"""

import uuid
import logging
from enum import Enum
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

class StepStatus(str, Enum):
    """Status states for workflow steps"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

@dataclass
class WorkflowStep:
    """
    Represents a single step in a workflow.
    
    Each step has a name, function to execute, status, and optional result.
    """
    name: str
    function: Callable
    description: str
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the step to a dictionary representation"""
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "result": self.result
        }
    
    def update_status(self, status: StepStatus) -> None:
        """Update the status of this step"""
        self.status = status
        logger.info(f"Step '{self.name}' status updated to {status}")

    def set_result(self, result: Any) -> None:
        """Set the result for this step"""
        self.result = result
        logger.debug(f"Step '{self.name}' result set")


class BaseWorkflow:
    """
    Base class for all workflows in the system.
    
    A workflow is a sequence of steps that are executed in order to achieve a goal.
    Each workflow has a unique ID, name, description, parameters, and a list of steps.
    """
    
    def __init__(self, name: str, description: str, parameters: Dict[str, Any] = None):
        """
        Initialize a new workflow.
        
        Args:
            name: The name of the workflow
            description: A description of what the workflow does
            parameters: Optional parameters for the workflow
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.parameters = parameters or {}
        self.steps: List[WorkflowStep] = []
        self.current_step_index = 0
        
        # Define the steps for this workflow
        self.define_steps()
        
        logger.info(f"Initialized workflow '{name}' with ID {self.id}")
    
    def define_steps(self) -> None:
        """
        Define the steps for this workflow.
        
        This method should be overridden by subclasses to define the specific 
        steps for their workflow.
        """
        raise NotImplementedError("Subclasses must implement define_steps")
    
    def add_step(self, name: str, function: Callable, description: str) -> None:
        """
        Add a step to the workflow.
        
        Args:
            name: The name of the step
            function: The function to execute for this step
            description: A description of what the step does
        """
        step = WorkflowStep(name=name, function=function, description=description)
        self.steps.append(step)
        logger.debug(f"Added step '{name}' to workflow '{self.name}'")
    
    def validate_parameters(self) -> bool:
        """
        Validate that all required parameters for the workflow are present and valid.
        
        Returns:
            True if all parameters are valid, False otherwise
        """
        # Base implementation always returns True
        # Subclasses should override this method to implement specific validation
        return True
    
    def execute_step(self, step_index: int) -> Dict[str, Any]:
        """
        Execute a specific step in the workflow.
        
        Args:
            step_index: The index of the step to execute
            
        Returns:
            A dictionary containing the step result and status
        """
        if step_index < 0 or step_index >= len(self.steps):
            error_msg = f"Step index {step_index} out of range for workflow '{self.name}'"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
        
        step = self.steps[step_index]
        step.update_status(StepStatus.RUNNING)
        
        try:
            logger.info(f"Executing step '{step.name}' in workflow '{self.name}'")
            result = step.function(self.parameters)
            step.set_result(result)
            step.update_status(StepStatus.COMPLETED)
            return {"status": "success", "result": result}
        except Exception as e:
            error_msg = f"Error executing step '{step.name}': {str(e)}"
            logger.error(error_msg, exc_info=True)
            step.update_status(StepStatus.FAILED)
            return {"status": "error", "message": error_msg}
    
    def execute_next_step(self) -> Dict[str, Any]:
        """
        Execute the next step in the workflow.
        
        Returns:
            A dictionary containing the step result and status
        """
        result = self.execute_step(self.current_step_index)
        if result["status"] == "success":
            self.current_step_index += 1
        return result
    
    def execute_all_steps(self) -> List[Dict[str, Any]]:
        """
        Execute all steps in the workflow.
        
        Returns:
            A list of dictionaries containing the results of each step
        """
        results = []
        self.current_step_index = 0
        
        while self.current_step_index < len(self.steps):
            result = self.execute_next_step()
            results.append(result)
            
            # Stop execution if a step fails
            if result["status"] == "error":
                break
        
        return results
    
    def get_step_status(self, step_index: int) -> Optional[StepStatus]:
        """
        Get the status of a specific step.
        
        Args:
            step_index: The index of the step
            
        Returns:
            The status of the step or None if the index is invalid
        """
        if 0 <= step_index < len(self.steps):
            return self.steps[step_index].status
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the workflow to a dictionary representation.
        
        Returns:
            A dictionary representing the workflow
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "steps": [step.to_dict() for step in self.steps],
            "current_step_index": self.current_step_index
        }
    
    def is_completed(self) -> bool:
        """
        Check if the workflow is completed.
        
        Returns:
            True if all steps are completed, False otherwise
        """
        return all(step.status == StepStatus.COMPLETED for step in self.steps)
    
    def reset(self) -> None:
        """Reset the workflow to its initial state"""
        for step in self.steps:
            step.update_status(StepStatus.PENDING)
            step.result = None
        self.current_step_index = 0
        logger.info(f"Reset workflow '{self.name}'") 