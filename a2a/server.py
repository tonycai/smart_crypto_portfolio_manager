"""
A2A Server Implementation for Smart Crypto Portfolio Manager

This module provides a server implementation for agents to expose their capabilities
to other agents using the Agent-to-Agent (A2A) protocol.
"""

import json
import uuid
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

from fastapi import FastAPI, HTTPException, BackgroundTasks, Response, status
from pydantic import BaseModel, Field


class Task(BaseModel):
    """Model for an A2A task."""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    capability: str
    parameters: Dict[str, Any]
    priority: str = "medium"
    callback_url: Optional[str] = None
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class MessagePart(BaseModel):
    """Model for a part in an A2A message."""
    type: str
    content: str
    filename: Optional[str] = None


class Message(BaseModel):
    """Model for an A2A message."""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    from_agent: str
    to_agent: str
    content: Dict[str, Any]
    parts: Optional[List[MessagePart]] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class A2AServer:
    """Server implementation for the A2A protocol."""
    
    def __init__(self, agent_card_path: str):
        """
        Initialize the A2A server.
        
        Args:
            agent_card_path: Path to the agent card JSON file
        """
        self.app = FastAPI(title="A2A Server")
        self.tasks = {}  # In-memory storage for tasks
        self.messages = {}  # In-memory storage for messages
        
        # Load agent card from file
        with open(agent_card_path, 'r') as f:
            self.agent_card = json.load(f)
        
        self.capability_handlers = {}
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register the API routes for the A2A protocol."""
        
        # Agent discovery
        @self.app.get("/api/v1/agent")
        async def get_agent_card():
            return self.agent_card
        
        # Task management
        @self.app.post("/api/v1/tasks", status_code=status.HTTP_201_CREATED)
        async def create_task(task: Task, background_tasks: BackgroundTasks):
            if task.capability not in self.capability_handlers:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Capability {task.capability} not supported"
                )
            
            # Store the task
            self.tasks[task.task_id] = task
            
            # Initialize messages list for this task
            self.messages[task.task_id] = []
            
            # Process the task in the background
            background_tasks.add_task(self._process_task, task)
            
            return task
        
        @self.app.get("/api/v1/tasks/{task_id}")
        async def get_task(task_id: str):
            if task_id not in self.tasks:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task {task_id} not found"
                )
            
            return self.tasks[task_id]
        
        @self.app.put("/api/v1/tasks/{task_id}")
        async def update_task(task_id: str, task_update: Dict[str, Any]):
            if task_id not in self.tasks:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task {task_id} not found"
                )
            
            task = self.tasks[task_id]
            
            # Update allowed fields
            allowed_fields = ["status", "result", "error"]
            for field in allowed_fields:
                if field in task_update:
                    setattr(task, field, task_update[field])
            
            # Update the timestamp
            task.updated_at = datetime.utcnow().isoformat()
            
            return task
        
        @self.app.delete("/api/v1/tasks/{task_id}")
        async def delete_task(task_id: str):
            if task_id not in self.tasks:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task {task_id} not found"
                )
            
            # Mark as canceled instead of deleting
            task = self.tasks[task_id]
            task.status = "canceled"
            task.updated_at = datetime.utcnow().isoformat()
            
            return {"message": f"Task {task_id} canceled"}
        
        # Messaging
        @self.app.post("/api/v1/tasks/{task_id}/messages", status_code=status.HTTP_201_CREATED)
        async def send_message(task_id: str, message: Message):
            if task_id not in self.tasks:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task {task_id} not found"
                )
            
            if message.task_id != task_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Message task_id does not match URL task_id"
                )
            
            # Store the message
            if task_id not in self.messages:
                self.messages[task_id] = []
            
            self.messages[task_id].append(message)
            
            return message
        
        @self.app.get("/api/v1/tasks/{task_id}/messages")
        async def get_messages(task_id: str):
            if task_id not in self.tasks:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task {task_id} not found"
                )
            
            if task_id not in self.messages:
                return []
            
            return self.messages[task_id]
    
    def register_capability_handler(self, capability: str, handler: Callable):
        """
        Register a handler function for a specific capability.
        
        Args:
            capability: The name of the capability
            handler: The function that handles tasks for this capability
        """
        self.capability_handlers[capability] = handler
    
    async def _process_task(self, task: Task):
        """
        Process a task using the registered capability handler.
        
        Args:
            task: The task to process
        """
        try:
            # Update task status to in_progress
            task.status = "in_progress"
            task.updated_at = datetime.utcnow().isoformat()
            
            # Get the handler for this capability
            handler = self.capability_handlers.get(task.capability)
            if not handler:
                raise ValueError(f"No handler registered for capability {task.capability}")
            
            # Execute the handler
            result = await handler(task.parameters)
            
            # Update task with result
            task.result = result
            task.status = "completed"
        except Exception as e:
            # Handle any errors
            task.error = {
                "message": str(e),
                "type": type(e).__name__
            }
            task.status = "failed"
        finally:
            # Update the timestamp
            task.updated_at = datetime.utcnow().isoformat()
            
            # Send callback if provided
            if task.callback_url:
                # In a real implementation, make an HTTP request to the callback URL
                pass


def create_a2a_server(agent_card_path: str) -> A2AServer:
    """
    Create and return an A2A server instance.
    
    Args:
        agent_card_path: Path to the agent card JSON file
        
    Returns:
        The A2A server instance
    """
    return A2AServer(agent_card_path)
