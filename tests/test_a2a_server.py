"""
Unit tests for testing the A2A Server implementation.

This module contains tests to validate the functionality of the A2A server,
including agent discovery, task management, message handling, and capability
registration.
"""

import unittest
import json
import os
import tempfile
from unittest.mock import patch, AsyncMock, MagicMock
import uuid
from datetime import datetime

from tests.custom_test_client import CustomTestClient

from src.a2a.server import A2AServer, Task, Message, MessagePart, create_a2a_server


class TestA2AServer(unittest.TestCase):
    """Test cases for the A2A Server implementation."""

    def setUp(self):
        """Set up test fixtures, creating sample agent card and server instance."""
        # Create a temporary agent card file
        self.agent_card = {
            "name": "TestAgent",
            "version": "1.0.0",
            "description": "A test agent for A2A protocol",
            "endpoint": "http://localhost:8000/api/v1/tasks",
            "capabilities": [
                {
                    "name": "test_capability",
                    "description": "A test capability",
                    "parameters": {
                        "param1": {"type": "string", "description": "A test parameter"}
                    },
                    "returns": {"type": "object", "description": "Test result"}
                }
            ]
        }
        
        # Create a temporary file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False)
        json.dump(self.agent_card, self.temp_file)
        self.temp_file.close()
        
        # Create the server
        self.server = A2AServer(self.temp_file.name)
        
        # Initialize test client with CustomTestClient
        self.client = CustomTestClient(self.server.app)
        
        # Set up test data
        self.test_task = Task(
            task_id=str(uuid.uuid4()),
            capability="test_capability",
            parameters={"param1": "test_value"}
        )
        
        self.test_message = Message(
            message_id=str(uuid.uuid4()),
            task_id=self.test_task.task_id,
            from_agent="OtherAgent",
            to_agent="TestAgent",
            content={"text": "Test message content"}
        )
        
        # Register a test capability handler
        async def test_handler(parameters):
            return {"result": f"Processed {parameters['param1']}"}
        
        self.server.register_capability_handler("test_capability", test_handler)
        
    def tearDown(self):
        """Tear down test fixtures, delete temporary files."""
        os.unlink(self.temp_file.name)
    
    def test_root_endpoint(self):
        """Test the root endpoint returns basic agent info."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "TestAgent")
        self.assertEqual(data["version"], "1.0.0")
        self.assertEqual(data["status"], "online")
        self.assertIn("test_capability", data["capabilities"])
        self.assertIn("timestamp", data)
    
    def test_get_agent_card(self):
        """Test retrieving the agent card."""
        response = self.client.get("/api/v1/agent")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.agent_card)
    
    def test_create_task(self):
        """Test creating a new task."""
        with patch.object(self.server, '_process_task', AsyncMock()) as mock_process:
            response = self.client.post(
                "/api/v1/tasks",
                json={
                    "capability": "test_capability",
                    "parameters": {"param1": "test_value"},
                    "priority": "high"
                }
            )
            self.assertEqual(response.status_code, 201)
            data = response.json()
            self.assertEqual(data["capability"], "test_capability")
            self.assertEqual(data["parameters"], {"param1": "test_value"})
            self.assertEqual(data["priority"], "high")
            self.assertEqual(data["status"], "pending")
            self.assertIsNotNone(data["task_id"])
            self.assertIsNotNone(data["created_at"])
            self.assertIsNotNone(data["updated_at"])
            
            # Verify the background task was triggered
            mock_process.assert_called_once()
    
    def test_create_task_invalid_capability(self):
        """Test creating a task with an invalid capability."""
        response = self.client.post(
            "/api/v1/tasks",
            json={
                "capability": "invalid_capability",
                "parameters": {"param1": "test_value"}
            }
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("not supported", response.json()["detail"])
    
    def test_get_task(self):
        """Test retrieving a task by ID."""
        # First create a task
        with patch.object(self.server, '_process_task', AsyncMock()):
            create_response = self.client.post(
                "/api/v1/tasks",
                json={
                    "capability": "test_capability",
                    "parameters": {"param1": "test_value"}
                }
            )
            task_id = create_response.json()["task_id"]
        
        # Now retrieve it
        get_response = self.client.get(f"/api/v1/tasks/{task_id}")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json()["task_id"], task_id)
    
    def test_get_task_not_found(self):
        """Test retrieving a non-existent task."""
        response = self.client.get(f"/api/v1/tasks/{uuid.uuid4()}")
        self.assertEqual(response.status_code, 404)
    
    def test_update_task(self):
        """Test updating a task's status and result."""
        # First create a task
        with patch.object(self.server, '_process_task', AsyncMock()):
            create_response = self.client.post(
                "/api/v1/tasks",
                json={
                    "capability": "test_capability",
                    "parameters": {"param1": "test_value"}
                }
            )
            task_id = create_response.json()["task_id"]
        
        # Now update it
        update_response = self.client.put(
            f"/api/v1/tasks/{task_id}",
            json={
                "status": "completed",
                "result": {"output": "test_result"}
            }
        )
        self.assertEqual(update_response.status_code, 200)
        updated_task = update_response.json()
        self.assertEqual(updated_task["status"], "completed")
        self.assertEqual(updated_task["result"], {"output": "test_result"})
    
    def test_cancel_task(self):
        """Test canceling a task."""
        # First create a task
        with patch.object(self.server, '_process_task', AsyncMock()):
            create_response = self.client.post(
                "/api/v1/tasks",
                json={
                    "capability": "test_capability",
                    "parameters": {"param1": "test_value"}
                }
            )
            task_id = create_response.json()["task_id"]
        
        # Now cancel it
        delete_response = self.client.delete(f"/api/v1/tasks/{task_id}")
        self.assertEqual(delete_response.status_code, 200)
        self.assertIn("canceled", delete_response.json()["message"])
        
        # Verify the task is marked as canceled
        task_response = self.client.get(f"/api/v1/tasks/{task_id}")
        self.assertEqual(task_response.json()["status"], "canceled")
    
    def test_send_message(self):
        """Test sending a message for a task."""
        # First create a task
        with patch.object(self.server, '_process_task', AsyncMock()):
            create_response = self.client.post(
                "/api/v1/tasks",
                json={
                    "capability": "test_capability",
                    "parameters": {"param1": "test_value"}
                }
            )
            task_id = create_response.json()["task_id"]
        
        # Now send a message
        message_response = self.client.post(
            f"/api/v1/tasks/{task_id}/messages",
            json={
                "message_id": str(uuid.uuid4()),
                "task_id": task_id,
                "from_agent": "OtherAgent",
                "to_agent": "TestAgent",
                "content": {"text": "Test message"}
            }
        )
        self.assertEqual(message_response.status_code, 201)
        self.assertEqual(message_response.json()["content"]["text"], "Test message")
    
    def test_send_message_with_parts(self):
        """Test sending a message with additional parts."""
        # First create a task
        with patch.object(self.server, '_process_task', AsyncMock()):
            create_response = self.client.post(
                "/api/v1/tasks",
                json={
                    "capability": "test_capability",
                    "parameters": {"param1": "test_value"}
                }
            )
            task_id = create_response.json()["task_id"]
        
        # Now send a message with parts
        message_response = self.client.post(
            f"/api/v1/tasks/{task_id}/messages",
            json={
                "message_id": str(uuid.uuid4()),
                "task_id": task_id,
                "from_agent": "OtherAgent",
                "to_agent": "TestAgent",
                "content": {"text": "Test message with attachment"},
                "parts": [
                    {
                        "type": "text/plain",
                        "content": "Plain text content",
                        "filename": "test.txt"
                    }
                ]
            }
        )
        self.assertEqual(message_response.status_code, 201)
        self.assertEqual(len(message_response.json()["parts"]), 1)
        self.assertEqual(message_response.json()["parts"][0]["filename"], "test.txt")
    
    def test_get_messages(self):
        """Test retrieving messages for a task."""
        # First create a task
        with patch.object(self.server, '_process_task', AsyncMock()):
            create_response = self.client.post(
                "/api/v1/tasks",
                json={
                    "capability": "test_capability",
                    "parameters": {"param1": "test_value"}
                }
            )
            task_id = create_response.json()["task_id"]
        
        # Send a couple of messages
        for i in range(2):
            self.client.post(
                f"/api/v1/tasks/{task_id}/messages",
                json={
                    "message_id": str(uuid.uuid4()),
                    "task_id": task_id,
                    "from_agent": "OtherAgent",
                    "to_agent": "TestAgent",
                    "content": {"text": f"Test message {i+1}"}
                }
            )
        
        # Now retrieve all messages
        messages_response = self.client.get(f"/api/v1/tasks/{task_id}/messages")
        self.assertEqual(messages_response.status_code, 200)
        messages = messages_response.json()
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["content"]["text"], "Test message 1")
        self.assertEqual(messages[1]["content"]["text"], "Test message 2")
    
    def test_process_task(self):
        """Test the task processing function."""
        task = Task(
            task_id=str(uuid.uuid4()),
            capability="test_capability",
            parameters={"param1": "test_value"}
        )
        
        # Create an async context for testing the async method
        import asyncio
        
        async def run_test():
            # Store task in task_registry using task_id as key instead of Task object
            self.server.task_registry[task.task_id] = task
            await self.server._process_task(task)
            self.assertEqual(task.status, "completed")
            self.assertEqual(task.result, {"result": "Processed test_value"})
        
        # Run the coroutine
        asyncio.run(run_test())
    
    def test_process_task_error(self):
        """Test task processing with an error."""
        task = Task(
            task_id=str(uuid.uuid4()),
            capability="test_capability",
            parameters={"param1": "test_value"}
        )
        
        # Register a handler that raises an exception
        async def error_handler(parameters):
            raise ValueError("Test error")
        
        self.server.register_capability_handler("test_capability", error_handler)
        
        # Create an async context for testing
        import asyncio
        
        async def run_test():
            # Store task in task_registry using task_id as key instead of Task object
            self.server.task_registry[task.task_id] = task
            await self.server._process_task(task)
            self.assertEqual(task.status, "failed")
            self.assertIn("message", task.error)
            self.assertEqual(task.error["type"], "ValueError")
            self.assertEqual(task.error["message"], "Test error")
        
        # Run the coroutine
        asyncio.run(run_test())
    
    def test_create_a2a_server_factory(self):
        """Test the factory function for creating an A2A server."""
        server = create_a2a_server(self.temp_file.name)
        self.assertIsInstance(server, A2AServer)
        # Use the correct attribute to access the agent config
        self.assertEqual(server.agent_config, self.agent_card)


if __name__ == "__main__":
    unittest.main() 