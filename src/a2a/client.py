"""
A2A Client Implementation for Smart Crypto Portfolio Manager

This module implements a client for Google's Agent-to-Agent (A2A) protocol,
allowing our system to communicate with other A2A-compatible agents.
"""
import json
import uuid
import requests
import logging
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class A2AClient:
    """Client for interacting with A2A-compatible agents."""
    
    def __init__(self, server_url: str):
        """
        Initialize the A2A client.
        
        Args:
            server_url: Base URL of the A2A server (without trailing slash)
        """
        self.server_url = server_url
        self.agent_card = None
        
    def discover_agent(self) -> Dict:
        """
        Fetch the Agent Card to discover capabilities.
        
        Returns:
            Dict containing the Agent Card information
        """
        try:
            response = requests.get(f"{self.server_url}/.well-known/agent.json")
            response.raise_for_status()
            self.agent_card = response.json()
            logger.info(f"Discovered agent: {self.agent_card.get('name', 'Unknown Agent')}")
            return self.agent_card
        except Exception as e:
            logger.error(f"Error discovering agent: {e}")
            raise
    
    def send_task(self, message_text: str, task_id: Optional[str] = None) -> Dict:
        """
        Send a task to the A2A server.
        
        Args:
            message_text: Text message to send to the agent
            task_id: Optional task ID (will generate a new one if not provided)
            
        Returns:
            Dict containing the task response
        """
        if task_id is None:
            task_id = str(uuid.uuid4())
            
        task_request = {
            "task_id": task_id,
            "message": {
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": message_text
                    }
                ]
            }
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/api/v1/tasks/send",
                json=task_request
            )
            response.raise_for_status()
            
            task_response = response.json()
            logger.info(f"Task {task_id} submitted with status: {task_response.get('status')}")
            return task_response
        except Exception as e:
            logger.error(f"Error sending task: {e}")
            raise
    
    def get_task(self, task_id: str) -> Dict:
        """
        Get the current state of a task.
        
        Args:
            task_id: ID of the task to retrieve
            
        Returns:
            Dict containing the task information
        """
        try:
            response = requests.get(f"{self.server_url}/api/v1/tasks/{task_id}")
            response.raise_for_status()
            
            task_response = response.json()
            logger.info(f"Task {task_id} status: {task_response.get('status')}")
            return task_response
        except Exception as e:
            logger.error(f"Error getting task: {e}")
            raise
    
    def cancel_task(self, task_id: str) -> Dict:
        """
        Cancel a task.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            Dict containing the cancel response
        """
        try:
            response = requests.delete(f"{self.server_url}/api/v1/tasks/{task_id}")
            response.raise_for_status()
            
            cancel_response = response.json()
            logger.info(f"Task {task_id} canceled with status: {cancel_response.get('status')}")
            return cancel_response
        except Exception as e:
            logger.error(f"Error canceling task: {e}")
            raise
    
    def get_latest_agent_message(self, task: Dict) -> Optional[Dict]:
        """
        Extract the latest agent message from a task.
        
        Args:
            task: Task object returned from send_task or get_task
            
        Returns:
            Dict containing the latest agent message or None
        """
        messages = task.get("messages", [])
        agent_messages = [m for m in messages if m.get("role") == "agent"]
        
        if agent_messages:
            return agent_messages[-1]
        return None
    
    def get_all_artifacts(self, task: Dict) -> List[Dict]:
        """
        Extract all artifacts from a task.
        
        Args:
            task: Task object returned from send_task or get_task
            
        Returns:
            List of artifact objects
        """
        return task.get("artifacts", [])
    
    def execute_skill(self, skill_name: str, skill_inputs: Dict, wait_for_completion: bool = True) -> Dict:
        """
        Execute a specific skill on the agent.
        
        Args:
            skill_name: Name of the skill to execute
            skill_inputs: Dictionary of input parameters for the skill
            wait_for_completion: Whether to wait for the task to complete
            
        Returns:
            Dict containing the task response
        """
        if not self.agent_card:
            self.discover_agent()
            
        # Verify the skill is available
        available_skills = [skill["name"] for skill in self.agent_card.get("skills", [])]
        if skill_name not in available_skills:
            raise ValueError(f"Skill '{skill_name}' not found in agent capabilities")
        
        # Prepare a structured message
        message_text = f"Execute skill: {skill_name}"
        
        task_request = {
            "task_id": str(uuid.uuid4()),
            "message": {
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": message_text
                    },
                    {
                        "type": "data",
                        "data": {
                            "skill": skill_name,
                            "inputs": skill_inputs
                        }
                    }
                ]
            }
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/api/v1/tasks/send",
                json=task_request
            )
            response.raise_for_status()
            
            task_response = response.json()
            task_id = task_response.get("task_id")
            logger.info(f"Skill execution task {task_id} submitted with status: {task_response.get('status')}")
            
            # Wait for completion if requested
            if wait_for_completion and task_response.get("status") not in ["completed", "failed", "canceled"]:
                while True:
                    task_response = self.get_task(task_id)
                    if task_response.get("status") in ["completed", "failed", "canceled"]:
                        break
                    import time
                    time.sleep(1)
            
            return task_response
        except Exception as e:
            logger.error(f"Error executing skill: {e}")
            raise


def main():
    """
    Example usage of the A2A client.
    """
    # Create a client for our local A2A server
    client = A2AClient("http://localhost:8000")
    
    # Discover agent capabilities
    agent_info = client.discover_agent()
    print(f"Connected to agent: {agent_info.get('name')}")
    print(f"Available skills: {[skill['name'] for skill in agent_info.get('skills', [])]}")
    
    # Send a task
    task = client.send_task("Give me a market analysis for Bitcoin and Ethereum")
    task_id = task["task_id"]
    
    # Wait for completion and get result
    while task["status"] not in ["completed", "failed", "canceled"]:
        task = client.get_task(task_id)
        print(f"Task status: {task['status']}")
        import time
        time.sleep(1)
    
    # Get the agent's response
    agent_message = client.get_latest_agent_message(task)
    if agent_message:
        for part in agent_message["parts"]:
            if part.get("type") == "text":
                print("\nAgent response:")
                print(part["text"])
    
    # Get artifacts
    artifacts = client.get_all_artifacts(task)
    print(f"\nTask generated {len(artifacts)} artifacts")
    for artifact in artifacts:
        print(f"- {artifact.get('display_name')}: {artifact.get('type')}")


if __name__ == "__main__":
    main() 