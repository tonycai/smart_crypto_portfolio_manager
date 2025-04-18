"""
Unit tests for the A2A client and server integration

This module contains tests to validate the integration between the A2A client and server
implementations. The tests ensure that the client can properly communicate with the server
and that both components work together as expected throughout the entire communication cycle.
"""
import unittest
import json
import time
import uuid
import threading
from unittest.mock import patch, MagicMock, mock_open
import requests
import httpx
from starlette.testclient import TestClient
import uvicorn

from src.a2a.client import A2AClient
from src.a2a.server import app, tasks_db


class TestA2AClientServerIntegration(unittest.TestCase):
    """Test the integration between A2A client and server implementations."""

    @classmethod
    def setUpClass(cls):
        """Set up for all tests."""
        # Initialize test client directly with httpx
        cls.test_client = httpx.Client(
            base_url="http://testserver",
            transport=httpx.ASGITransport(app=app)
        )
        
        # Clear the tasks_db before each test class execution
        tasks_db.clear()
        
        # Create a sample agent card for tests
        cls.sample_agent_card = {
            "name": "Smart Crypto Portfolio Manager",
            "description": "An agent for managing cryptocurrency portfolios",
            "version": "1.0.0",
            "api_version": "v1",
            "contact_email": "support@cryptoportfolio.example",
            "skills": [
                {
                    "name": "market_analysis",
                    "description": "Analyze cryptocurrency market trends and provide insights"
                },
                {
                    "name": "trade_execution",
                    "description": "Execute cryptocurrency trades on behalf of the user"
                },
                {
                    "name": "risk_assessment",
                    "description": "Assess the risk level of a potential cryptocurrency trade"
                }
            ]
        }

    def setUp(self):
        """Set up test case."""
        # Clear tasks_db before each test
        tasks_db.clear()
            
        # Set up A2A client pointing to FastAPI test client
        self.client = A2AClient("http://testserver")
        
        # Mock the agent.json file
        self.agent_json_patcher = patch("builtins.open", mock_open(
            read_data=json.dumps(self.sample_agent_card)
        ))
        self.mock_agent_json = self.agent_json_patcher.start()

    def tearDown(self):
        """Clean up after test case."""
        self.agent_json_patcher.stop()

    @patch("src.a2a.client.requests.get")
    def test_client_discover_agent(self, mock_get):
        """Test client discovery of agent capabilities through the server."""
        # Set up the mock response
        mock_response = MagicMock()
        mock_response.json.return_value = self.sample_agent_card
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Make the actual request
        result = self.client.discover_agent()
        
        # Verify the result matches the expected agent card
        self.assertEqual(result, self.sample_agent_card)
        self.assertEqual(result["name"], "Smart Crypto Portfolio Manager")
        self.assertEqual(len(result["skills"]), 3)
        mock_get.assert_called_once_with("http://testserver/.well-known/agent.json")

    def test_server_agent_card_endpoint(self):
        """Test that the server correctly serves the agent card."""
        with patch("builtins.open", mock_open(read_data=json.dumps(self.sample_agent_card))):
            response = self.test_client.get("/.well-known/agent.json")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), self.sample_agent_card)

    def test_client_server_send_task(self):
        """Test that client can send a task to the server and get a valid response."""
        # Test sending a task via the client to the server
        task_message = "Analyze Bitcoin market trends"
        task_id = str(uuid.uuid4())
        
        # Mock the requests.post call
        with patch("src.a2a.client.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "task_id": task_id,
                "status": "submitted",
                "messages": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "type": "text",
                                "text": task_message
                            }
                        ]
                    }
                ],
                "artifacts": [],
                "created_time": "2023-08-15T12:00:00",
                "updated_time": "2023-08-15T12:00:00"
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            # Make the client request
            task_response = self.client.send_task(task_message, task_id)
            
            # Verify the response
            self.assertEqual(task_response["task_id"], task_id)
            self.assertEqual(task_response["status"], "submitted")
            self.assertEqual(len(task_response["messages"]), 1)
            self.assertEqual(task_response["messages"][0]["role"], "user")
            self.assertEqual(task_response["messages"][0]["parts"][0]["text"], task_message)
            
            # Verify the post request was made correctly
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertEqual(args[0], "http://testserver/api/v1/tasks/send")
            self.assertEqual(kwargs["json"]["task_id"], task_id)
            self.assertEqual(kwargs["json"]["message"]["parts"][0]["text"], task_message)

    def test_server_handle_task_endpoint(self):
        """Test that the server properly handles a task request."""
        # Direct test of the server endpoint
        task_id = str(uuid.uuid4())
        task_request = {
            "task_id": task_id,
            "message": {
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": "Analyze Bitcoin market trends"
                    }
                ]
            }
        }
        
        response = self.test_client.post("/api/v1/tasks/send", json=task_request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["task_id"], task_id)
        self.assertEqual(response.json()["status"], "submitted")

    def test_client_server_get_task(self):
        """Test retrieving a task's status from the server using the client."""
        # First add a task to the server's tasks_db
        task_id = str(uuid.uuid4())
        tasks_db[task_id] = {
            "task_id": task_id,
            "status": "completed",
            "messages": [
                {
                    "role": "user",
                    "parts": [{"type": "text", "text": "Analyze Bitcoin market trends"}]
                },
                {
                    "role": "agent",
                    "parts": [{"type": "text", "text": "Bitcoin is showing a bullish trend today."}]
                }
            ],
            "artifacts": [],
            "created_time": "2023-08-15T12:00:00",
            "updated_time": "2023-08-15T12:01:00"
        }
        
        # Mock the requests.get call in the client
        with patch("src.a2a.client.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = tasks_db[task_id]
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Get the task using the client
            task_result = self.client.get_task(task_id)
            
            # Verify the result
            self.assertEqual(task_result["task_id"], task_id)
            self.assertEqual(task_result["status"], "completed")
            self.assertEqual(len(task_result["messages"]), 2)
            
            # Verify the get request was made correctly
            mock_get.assert_called_once_with(f"http://testserver/api/v1/tasks/{task_id}")

    def test_server_get_task_endpoint(self):
        """Test that the server's task retrieval endpoint works correctly."""
        # Add a task to the server's tasks_db
        task_id = str(uuid.uuid4())
        tasks_db[task_id] = {
            "task_id": task_id,
            "status": "working",
            "messages": [
                {
                    "role": "user",
                    "parts": [{"type": "text", "text": "Analyze Ethereum market trends"}]
                }
            ],
            "artifacts": [],
            "created_time": "2023-08-15T12:00:00",
            "updated_time": "2023-08-15T12:00:00"
        }
        
        # Test the GET endpoint
        response = self.test_client.get(f"/api/v1/tasks/{task_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["task_id"], task_id)
        self.assertEqual(response.json()["status"], "working")

    def test_server_task_not_found(self):
        """Test the server's response when a task is not found."""
        # Test with a non-existent task ID
        non_existent_id = str(uuid.uuid4())
        response = self.test_client.get(f"/api/v1/tasks/{non_existent_id}")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Task not found", response.json()["detail"])

    def test_client_server_cancel_task(self):
        """Test canceling a task using the client."""
        # Add a task to the server's tasks_db
        task_id = str(uuid.uuid4())
        tasks_db[task_id] = {
            "task_id": task_id,
            "status": "working",
            "messages": [
                {
                    "role": "user",
                    "parts": [{"type": "text", "text": "Analyze Ethereum market trends"}]
                }
            ],
            "artifacts": [],
            "created_time": "2023-08-15T12:00:00",
            "updated_time": "2023-08-15T12:00:00"
        }
        
        # Mock the requests.delete call in the client
        with patch("src.a2a.client.requests.delete") as mock_delete:
            mock_response = MagicMock()
            mock_response.json.return_value = {"task_id": task_id, "status": "canceled"}
            mock_response.raise_for_status.return_value = None
            mock_delete.return_value = mock_response
            
            # Cancel the task using the client
            cancel_result = self.client.cancel_task(task_id)
            
            # Verify the result
            self.assertEqual(cancel_result["task_id"], task_id)
            self.assertEqual(cancel_result["status"], "canceled")
            
            # Verify the delete request was made correctly
            mock_delete.assert_called_once_with(f"http://testserver/api/v1/tasks/{task_id}")

    def test_server_cancel_task_endpoint(self):
        """Test the server's task cancellation endpoint."""
        # Add a task to the server's tasks_db
        task_id = str(uuid.uuid4())
        tasks_db[task_id] = {
            "task_id": task_id,
            "status": "working",
            "messages": [
                {
                    "role": "user",
                    "parts": [{"type": "text", "text": "Analyze Ethereum market trends"}]
                }
            ],
            "artifacts": [],
            "created_time": "2023-08-15T12:00:00",
            "updated_time": "2023-08-15T12:00:00"
        }
        
        # Test the DELETE endpoint
        response = self.test_client.delete(f"/api/v1/tasks/{task_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["task_id"], task_id)
        self.assertEqual(response.json()["status"], "canceled")
        
        # Verify the task status was updated in the server's tasks_db
        self.assertEqual(tasks_db[task_id]["status"], "canceled")

    def test_full_task_lifecycle(self):
        """Test the complete lifecycle of a task from creation to response extraction."""
        task_id = str(uuid.uuid4())
        task_message = "Analyze Bitcoin market trends"
        
        # Mock the initial task submission
        with patch("src.a2a.client.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "task_id": task_id,
                "status": "submitted",
                "messages": [
                    {
                        "role": "user",
                        "parts": [{"type": "text", "text": task_message}]
                    }
                ],
                "artifacts": [],
                "created_time": "2023-08-15T12:00:00",
                "updated_time": "2023-08-15T12:00:00"
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            # Send the task
            task = self.client.send_task(task_message, task_id)
            self.assertEqual(task["status"], "submitted")
        
        # Mock task status check - first working, then completed
        with patch("src.a2a.client.requests.get") as mock_get:
            # First call - still working
            working_response = MagicMock()
            working_response.json.return_value = {
                "task_id": task_id,
                "status": "working",
                "messages": [
                    {
                        "role": "user",
                        "parts": [{"type": "text", "text": task_message}]
                    }
                ],
                "artifacts": [],
                "created_time": "2023-08-15T12:00:00",
                "updated_time": "2023-08-15T12:00:30"
            }
            working_response.raise_for_status.return_value = None
            
            # Second call - completed with agent response
            completed_response = MagicMock()
            completed_response.json.return_value = {
                "task_id": task_id,
                "status": "completed",
                "messages": [
                    {
                        "role": "user",
                        "parts": [{"type": "text", "text": task_message}]
                    },
                    {
                        "role": "agent",
                        "parts": [{"type": "text", "text": "Bitcoin is showing a bullish trend with 5% gains today."}]
                    }
                ],
                "artifacts": [
                    {
                        "artifact_id": str(uuid.uuid4()),
                        "type": "chart",
                        "display_name": "Bitcoin Price Chart",
                        "mime_type": "image/png",
                        "data": "base64encodeddata"
                    }
                ],
                "created_time": "2023-08-15T12:00:00",
                "updated_time": "2023-08-15T12:01:00"
            }
            completed_response.raise_for_status.return_value = None
            
            # Set up the mock to return different responses on consecutive calls
            mock_get.side_effect = [working_response, completed_response]
            
            # First check - should be working
            task_status = self.client.get_task(task_id)
            self.assertEqual(task_status["status"], "working")
            
            # Second check - should be completed
            task_result = self.client.get_task(task_id)
            self.assertEqual(task_result["status"], "completed")
            
            # Get the agent message
            agent_message = self.client.get_latest_agent_message(task_result)
            self.assertIsNotNone(agent_message)
            self.assertEqual(agent_message["role"], "agent")
            self.assertEqual(agent_message["parts"][0]["text"], "Bitcoin is showing a bullish trend with 5% gains today.")
            
            # Get artifacts
            artifacts = self.client.get_all_artifacts(task_result)
            self.assertEqual(len(artifacts), 1)
            self.assertEqual(artifacts[0]["type"], "chart")
            self.assertEqual(artifacts[0]["display_name"], "Bitcoin Price Chart")

    def test_client_execute_skill(self):
        """Test executing a specific skill on the server using the client."""
        skill_name = "market_analysis"
        skill_inputs = {"asset": "BTC", "timeframe": "1d"}
        task_id = str(uuid.uuid4())
        
        # Mock the agent card discovery
        with patch("src.a2a.client.requests.get") as mock_get:
            mock_get_response = MagicMock()
            mock_get_response.json.return_value = self.sample_agent_card
            mock_get_response.raise_for_status.return_value = None
            mock_get.return_value = mock_get_response
            
            # Mock the skill execution request
            with patch("src.a2a.client.requests.post") as mock_post:
                mock_post_response = MagicMock()
                mock_post_response.json.return_value = {
                    "task_id": task_id,
                    "status": "completed",
                    "messages": [
                        {
                            "role": "user",
                            "parts": [
                                {"type": "text", "text": "Execute skill: market_analysis"},
                                {"type": "data", "data": {"skill": "market_analysis", "inputs": skill_inputs}}
                            ]
                        },
                        {
                            "role": "agent",
                            "parts": [{"type": "text", "text": "BTC showed strong upward momentum in the past 24 hours."}]
                        }
                    ],
                    "artifacts": [],
                    "created_time": "2023-08-15T12:00:00",
                    "updated_time": "2023-08-15T12:00:05"
                }
                mock_post_response.raise_for_status.return_value = None
                mock_post.return_value = mock_post_response
                
                # Execute the skill
                skill_result = self.client.execute_skill(skill_name, skill_inputs, wait_for_completion=False)
                
                # Verify the result
                self.assertEqual(skill_result["task_id"], task_id)
                self.assertEqual(skill_result["status"], "completed")
                
                # Verify that the correct request was made
                mock_post.assert_called_once()
                args, kwargs = mock_post.call_args
                self.assertEqual(args[0], "http://testserver/api/v1/tasks/send")
                self.assertEqual(kwargs["json"]["message"]["parts"][0]["text"], "Execute skill: market_analysis")
                self.assertEqual(kwargs["json"]["message"]["parts"][1]["data"]["skill"], "market_analysis")
                self.assertEqual(kwargs["json"]["message"]["parts"][1]["data"]["inputs"], skill_inputs)

    def test_client_invalid_skill(self):
        """Test client behavior when requesting an invalid skill."""
        # Mock the agent card discovery
        with patch("src.a2a.client.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = self.sample_agent_card
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Try to execute a non-existent skill
            with self.assertRaises(ValueError) as context:
                self.client.execute_skill("non_existent_skill", {})
            
            self.assertIn("not found in agent capabilities", str(context.exception))

    def test_error_handling(self):
        """Test error handling in client-server communication."""
        # Mock a network error when discovering agent
        with patch("src.a2a.client.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Failed to connect")
            
            with self.assertRaises(Exception) as context:
                self.client.discover_agent()
            
            self.assertIn("Error discovering agent", str(context.exception))
            
        # Mock a server error when sending task
        with patch("src.a2a.client.requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.HTTPError("500 Server Error")
            
            with self.assertRaises(Exception) as context:
                self.client.send_task("This will cause an error")
            
            self.assertIn("Error sending task", str(context.exception))


if __name__ == "__main__":
    unittest.main() 