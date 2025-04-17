"""
Utility functions shared across the application.
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configuration as a dictionary
    """
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config from {config_path}: {e}")
        raise

def generate_workflow_id() -> str:
    """Generate a unique workflow ID.
    
    Returns:
        Unique workflow ID string
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"workflow-{timestamp}"

def format_response(
    success: bool, 
    data: Optional[Any] = None, 
    error: Optional[str] = None
) -> Dict[str, Any]:
    """Format a standard response.
    
    Args:
        success: Whether the operation was successful
        data: Response data if successful
        error: Error message if not successful
        
    Returns:
        Formatted response dictionary
    """
    response = {
        "success": success,
        "timestamp": datetime.now().isoformat()
    }
    
    if success and data is not None:
        response["data"] = data
    
    if not success and error is not None:
        response["error"] = error
    
    return response 