"""
Unit tests for the A2A server implementation.

These tests validate that the A2A server correctly handles API endpoints, 
manages tasks, processes messages, and returns appropriate responses.
"""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import json
import uuid
from datetime import datetime
import asyncio

# FastAPI testing imports
from fastapi.testclient import TestClient
from fastapi import status

# Import the server module
from src.a2a.server import app, process_task, tasks_get, tasks_send_subscribe


class TestA2AServer(unittest.TestCase):
    """Test cases for the A2A server implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        
        # Sample task data
        self.task_id = str(uuid.uuid4())
        self.user_message = {
            "role": "user",
            "parts": [
                {
                    "type": "text",
                    "text": "Analyze BTC market trends"
                }
            ]
        }
        
        # Sample task request
        self.task_request = {
            "task_id": self.task_id,
            "message": self.user_message
        }
        
        # Sample completed task
        self.completed_task = {
            "task_id": self.task_id,
            "status": "completed",
            "messages": [
                self.user_message,
                {
                    "role": "agent",
                    "parts": [
                        {
                            "type": "text",
                            "text": "BTC is showing a bullish trend with strong volume."
                        }
                    ]
                }
            ],
            "artifacts": [
                {
                    "artifact_id": str(uuid.uuid4()),
                    "type": "market_analysis",
                    "mime_type": "application/json",
                    "display_name": "BTC Market Analysis",
                    "parts": [
                        {
                            "type": "data",
                            "data": {
                                "trend": "bullish",
                                "support_level": 65000,
                                "resistance_level": 68000,
                                "volume": "high"
                            }
                        }
                    ]
                }
            ],
            "created_time": datetime.utcnow().isoformat() + "Z",
            "updated_time": datetime.utcnow().isoformat() + "Z"
        }
        
        # Sample skill execution request
        self.skill_request = {
            "task_id": str(uuid.uuid4()),
            "message": {
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": "Execute skill: market_analysis"
                    },
                    {
                        "type": "data",
                        "data": {
                            "skill": "market_analysis",
                            "inputs": {
                                "assets": ["BTC", "ETH"]
                            }
                        }
                    }
                ]
            }
        }
    
    @patch('src.a2a.server.tasks', {})
    def test_tasks_get_nonexistent(self):
        """Test getting a nonexistent task."""
        response = self.client.get(f"/api/v1/tasks/{self.task_id}")
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["detail"], f"Task {self.task_id} not found")
    
    @patch('src.a2a.server.tasks')
    def test_tasks_get_existing(self, mock_tasks):
        """Test getting an existing task."""
        # Set up mock data
        mock_tasks.get.return_value = self.completed_task
        
        # Make request
        response = self.client.get(f"/api/v1/tasks/{self.task_id}")
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data["task_id"], self.task_id)
        self.assertEqual(response_data["status"], "completed")
        self.assertEqual(len(response_data["messages"]), 2)
        self.assertEqual(len(response_data["artifacts"]), 1)
    
    @patch('src.a2a.server.process_task')
    @patch('src.a2a.server.tasks', {})
    def test_tasks_send(self, mock_process_task):
        """Test sending a new task."""
        # Set up mock
        mock_process_task.return_value = asyncio.Future()
        mock_process_task.return_value.set_result(None)
        
        # Make request
        response = self.client.post(
            "/api/v1/tasks/send",
            json=self.task_request
        )
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        response_data = response.json()
        self.assertEqual(response_data["task_id"], self.task_id)
        self.assertEqual(response_data["status"], "submitted")
        self.assertEqual(len(response_data["messages"]), 1)
        self.assertEqual(response_data["messages"][0], self.user_message)
        
        # Verify process_task was called
        mock_process_task.assert_called_once()
    
    @patch('src.a2a.server.tasks')
    def test_tasks_cancel_existing(self, mock_tasks):
        """Test canceling an existing task."""
        # Set up mock data
        mock_tasks.get.return_value = {**self.completed_task, "status": "in_progress"}
        
        # Make request
        response = self.client.delete(f"/api/v1/tasks/{self.task_id}")
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data["task_id"], self.task_id)
        self.assertEqual(response_data["status"], "canceled")
    
    @patch('src.a2a.server.tasks')
    def test_tasks_cancel_nonexistent(self, mock_tasks):
        """Test canceling a nonexistent task."""
        # Set up mock to return None
        mock_tasks.get.return_value = None
        
        # Make request
        response = self.client.delete(f"/api/v1/tasks/{self.task_id}")
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["detail"], f"Task {self.task_id} not found")
    
    @patch('src.a2a.server.tasks', {})
    def test_agent_discovery(self):
        """Test agent discovery endpoint."""
        response = self.client.get("/.well-known/agent.json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        agent_data = response.json()
        
        # Check required fields
        self.assertIn("schema_version", agent_data)
        self.assertIn("name", agent_data)
        self.assertIn("description", agent_data)
        self.assertIn("contact", agent_data)
        self.assertIn("api", agent_data)
        self.assertIn("skills", agent_data)
        
        # Check skills are defined
        self.assertGreater(len(agent_data["skills"]), 0)
        
        # Check API info is correct
        self.assertIn("url", agent_data["api"])
        self.assertIn("auth", agent_data["api"])
    
    @patch('src.a2a.server.process_market_analysis')
    async def test_process_task_market_analysis(self, mock_market_analysis):
        """Test processing a market analysis task."""
        # Setup mock
        mock_market_analysis.return_value = {
            "analysis_result": "Bullish trend detected",
            "support_level": 65000,
            "resistance_level": 68000
        }
        
        # Create test task with market analysis text
        task = {
            "task_id": self.task_id,
            "status": "submitted",
            "messages": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "type": "text",
                            "text": "Analyze BTC market"
                        }
                    ]
                }
            ],
            "artifacts": [],
            "created_time": datetime.utcnow().isoformat() + "Z",
            "updated_time": datetime.utcnow().isoformat() + "Z"
        }
        
        # Process the task
        await process_task(task)
        
        # Assertions
        mock_market_analysis.assert_called_once()
        self.assertEqual(task["status"], "completed")
        self.assertEqual(len(task["messages"]), 2)  # Original + response
        self.assertGreaterEqual(len(task["artifacts"]), 1)
    
    @patch('src.a2a.server.process_trade_execution')
    async def test_process_task_trade_execution(self, mock_trade_execution):
        """Test processing a trade execution task."""
        # Setup mock
        mock_trade_execution.return_value = {
            "order_id": "12345",
            "status": "filled",
            "execution_price": 66500,
            "quantity": 0.5
        }
        
        # Create test task with trade execution text
        task = {
            "task_id": self.task_id,
            "status": "submitted",
            "messages": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "type": "text",
                            "text": "Execute BTC buy order at market price for 0.5 BTC"
                        }
                    ]
                }
            ],
            "artifacts": [],
            "created_time": datetime.utcnow().isoformat() + "Z",
            "updated_time": datetime.utcnow().isoformat() + "Z"
        }
        
        # Process the task
        await process_task(task)
        
        # Assertions
        mock_trade_execution.assert_called_once()
        self.assertEqual(task["status"], "completed")
        self.assertEqual(len(task["messages"]), 2)  # Original + response
        self.assertGreaterEqual(len(task["artifacts"]), 1)
    
    @patch('src.a2a.server.process_skill_execution')
    async def test_process_task_skill_execution(self, mock_skill_execution):
        """Test processing a skill execution task."""
        # Setup mock
        mock_skill_execution.return_value = {
            "result": "Skill executed successfully",
            "data": {"key": "value"}
        }
        
        # Create test task with skill execution message
        task = {
            "task_id": self.skill_request["task_id"],
            "status": "submitted",
            "messages": [self.skill_request["message"]],
            "artifacts": [],
            "created_time": datetime.utcnow().isoformat() + "Z",
            "updated_time": datetime.utcnow().isoformat() + "Z"
        }
        
        # Process the task
        await process_task(task)
        
        # Assertions
        mock_skill_execution.assert_called_once()
        self.assertEqual(task["status"], "completed")
        self.assertEqual(len(task["messages"]), 2)  # Original + response
        
        # Verify the skill name and inputs were correctly extracted
        call_args = mock_skill_execution.call_args[0]
        self.assertEqual(call_args[1], "market_analysis")
        self.assertEqual(call_args[2], {"assets": ["BTC", "ETH"]})
    
    @patch('src.a2a.server.process_task')
    @patch('src.a2a.server.tasks', {})
    async def test_skills_execution_missing_params(self, mock_process_task):
        """Test validation of skill execution with missing parameters."""
        # Create an invalid skill request missing the data part
        invalid_request = {
            "task_id": str(uuid.uuid4()),
            "message": {
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": "Execute skill: market_analysis"
                    }
                    # Missing the data part
                ]
            }
        }
        
        # Make request
        response = self.client.post(
            "/api/v1/tasks/send",
            json=invalid_request
        )
        
        # The request should be accepted as it's a valid task, even if the skill execution is invalid
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        
        # The task should be processed
        mock_process_task.assert_called_once()
        
        # The actual validation would happen in process_skill_execution
        # which would handle the missing parameters
    
    @patch('src.a2a.server.tasks')
    async def test_handle_error_in_task_processing(self, mock_tasks):
        """Test handling errors during task processing."""
        # Create a mock implementation of process_task that raises an exception
        async def mock_process_task_with_error(task):
            task["status"] = "error"
            task["error"] = "An error occurred during processing"
            raise Exception("Test exception")
        
        # Patch process_task with our mock implementation
        with patch('src.a2a.server.process_task', mock_process_task_with_error):
            # Set up task data
            task = {
                "task_id": self.task_id,
                "status": "submitted",
                "messages": [self.user_message],
                "artifacts": [],
                "created_time": datetime.utcnow().isoformat() + "Z",
                "updated_time": datetime.utcnow().isoformat() + "Z"
            }
            
            # Mock tasks.get to return our task
            mock_tasks.get.return_value = task
            
            # Make request to send the task
            response = self.client.post(
                "/api/v1/tasks/send",
                json=self.task_request
            )
            
            # The request should be accepted
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            
            # Allow some time for the task to be processed
            await asyncio.sleep(0.1)
            
            # Get the task status
            response = self.client.get(f"/api/v1/tasks/{self.task_id}")
            
            # The task should be in error state
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.json()["status"], "error")
            self.assertEqual(response.json()["error"], "An error occurred during processing")


if __name__ == '__main__':
    unittest.main() 