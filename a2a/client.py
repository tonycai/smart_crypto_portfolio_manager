"""
A2A Client Library for Smart Crypto Portfolio Manager

This module provides a client library for agents to communicate with other agents
using the Agent-to-Agent (A2A) protocol.
"""

import json
import uuid
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Union


class A2AClient:
    """Client for interacting with other agents using the A2A protocol."""
    
    def __init__(self, agent_name: str, agent_version: str):
        """
        Initialize the A2A client.
        
        Args:
            agent_name: The name of the agent using this client
            agent_version: The version of the agent
        """
        self.agent_name = agent_name
        self.agent_version = agent_version
        self.agent_registry = {}  # Store information about known agents
    
    def discover_agent(self, agent_url: str) -> Dict[str, Any]:
        """
        Discover an agent's capabilities by fetching its agent card.
        
        Args:
            agent_url: Base URL of the agent
            
        Returns:
            The agent card as a dictionary
        """
        discovery_url = f"{agent_url.rstrip('/')}/api/v1/agent"
        response = requests.get(discovery_url)
        response.raise_for_status()
        agent_card = response.json()
        
        # Store in registry for later use
        agent_endpoint = agent_card.get("endpoint")
        if agent_endpoint:
            self.agent_registry[agent_card["name"]] = agent_card
        
        return agent_card
    
    def create_task(
        self, 
        agent_name: str, 
        capability: str, 
        parameters: Dict[str, Any],
        priority: str = "medium",
        callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new task for another agent.
        
        Args:
            agent_name: Name of the agent to create a task for
            capability: The capability to invoke
            parameters: Parameters for the capability
            priority: Priority of the task (low, medium, high, critical)
            callback_url: Optional URL for callbacks on task status changes
            
        Returns:
            The created task object
        """
        if agent_name not in self.agent_registry:
            raise ValueError(f"Agent {agent_name} not found in registry. Discover it first.")
        
        agent_card = self.agent_registry[agent_name]
        endpoint = agent_card["endpoint"]
        
        # Check if the capability exists
        capability_exists = False
        for cap in agent_card.get("capabilities", []):
            if cap.get("name") == capability:
                capability_exists = True
                break
        
        if not capability_exists:
            raise ValueError(f"Capability {capability} not found in agent {agent_name}")
        
        # Create task payload
        task = {
            "task_id": str(uuid.uuid4()),
            "capability": capability,
            "parameters": parameters,
            "priority": priority,
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }
        
        if callback_url:
            task["callback_url"] = callback_url
        
        # Send request to create task
        response = requests.post(endpoint, json=task)
        response.raise_for_status()
        
        return response.json()
    
    def get_task(self, agent_name: str, task_id: str) -> Dict[str, Any]:
        """
        Get the details of a specific task.
        
        Args:
            agent_name: Name of the agent hosting the task
            task_id: ID of the task to retrieve
            
        Returns:
            The task object
        """
        if agent_name not in self.agent_registry:
            raise ValueError(f"Agent {agent_name} not found in registry")
        
        agent_card = self.agent_registry[agent_name]
        endpoint = agent_card["endpoint"]
        
        # Extract base path from endpoint
        base_url = endpoint.split("/api/v1/tasks")[0] if "/api/v1/tasks" in endpoint else endpoint
        task_url = f"{base_url}/api/v1/tasks/{task_id}"
        
        response = requests.get(task_url)
        response.raise_for_status()
        
        return response.json()
    
    def send_message(
        self,
        agent_name: str,
        task_id: str,
        content: Dict[str, Any],
        parts: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send a message related to a task.
        
        Args:
            agent_name: Name of the receiving agent
            task_id: ID of the task the message relates to
            content: Content of the message
            parts: Additional parts of the message (e.g., files)
            
        Returns:
            The created message object
        """
        if agent_name not in self.agent_registry:
            raise ValueError(f"Agent {agent_name} not found in registry")
        
        agent_card = self.agent_registry[agent_name]
        endpoint = agent_card["endpoint"]
        
        # Extract base path from endpoint
        base_url = endpoint.split("/api/v1/tasks")[0] if "/api/v1/tasks" in endpoint else endpoint
        message_url = f"{base_url}/api/v1/tasks/{task_id}/messages"
        
        # Create message payload
        message = {
            "message_id": str(uuid.uuid4()),
            "task_id": task_id,
            "from_agent": self.agent_name,
            "to_agent": agent_name,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if parts:
            message["parts"] = parts
        
        response = requests.post(message_url, json=message)
        response.raise_for_status()
        
        return response.json()
    
    def get_messages(self, agent_name: str, task_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages for a task.
        
        Args:
            agent_name: Name of the agent hosting the task
            task_id: ID of the task
            
        Returns:
            List of message objects
        """
        if agent_name not in self.agent_registry:
            raise ValueError(f"Agent {agent_name} not found in registry")
        
        agent_card = self.agent_registry[agent_name]
        endpoint = agent_card["endpoint"]
        
        # Extract base path from endpoint
        base_url = endpoint.split("/api/v1/tasks")[0] if "/api/v1/tasks" in endpoint else endpoint
        messages_url = f"{base_url}/api/v1/tasks/{task_id}/messages"
        
        response = requests.get(messages_url)
        response.raise_for_status()
        
        return response.json()