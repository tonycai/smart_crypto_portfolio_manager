"""
Unit tests for the A2A client implementation.

These tests validate that the A2A client correctly communicates with A2A-compatible servers,
handles responses appropriately, and manages tasks and artifacts as expected.
"""
import unittest
from unittest.mock import patch, MagicMock
import json
import uuid
import requests
from src.a2a.client import A2AClient


class TestA2AClient(unittest.TestCase):
    """Test cases for the A2A client implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.server_url = "http://test-server:8000"
        self.client = A2AClient(self.server_url)
        
        # Sample agent card
        self.agent_card = {
            "schema_version": "1.0",
            "name": "Test Agent",
            "description": "A test agent for unit testing",
            "contact": {
                "name": "Test Developer",
                "url": "https://example.com",
                "email": "test@example.com"
            },
            "api": {
                "url": "http://test-server:8000",
                "auth": {
                    "type": "none"
                }
            },
            "skills": [
                {
                    "name": "market_analysis",
                    "description": "Analyze market conditions for cryptocurrencies",
                    "inputs": {
                        "assets": {
                            "type": "array",
                            "description": "List of assets to analyze"
                        }
                    },
                    "outputs": {
                        "analysis": {
                            "type": "object",
                            "description": "Market analysis results"
                        }
                    }
                }
            ]
        }
        
        # Sample task response
        self.task_response = {
            "task_id": str(uuid.uuid4()),
            "status": "completed",
            "messages": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "type": "text",
                            "text": "Analyze BTC market"
                        }
                    ]
                },
                {
                    "role": "agent",
                    "parts": [
                        {
                            "type": "text",
                            "text": "BTC is showing a bullish trend with strong support at $65,000."
                        }
                    ]
                }
            ],
            "artifacts": [
                {
                    "artifact_id": str(uuid.uuid4()),
                    "type": "crypto_chart",
                    "mime_type": "application/json",
                    "display_name": "BTC Price Chart",
                    "parts": [
                        {
                            "type": "data",
                            "data": {
                                "description": "BTC Price Chart for the last 7 days",
                                "chart_type": "line",
                                "data_points": [
                                    {"date": "2023-06-01", "price": 65200},
                                    {"date": "2023-06-07", "price": 67800}
                                ]
                            }
                        }
                    ]
                }
            ],
            "created_time": "2023-06-07T12:00:00Z",
            "updated_time": "2023-06-07T12:01:00Z"
        }
    
    @patch('requests.get')
    def test_discover_agent(self, mock_get):
        """Test that the client can discover an agent's capabilities."""
        # Configure the mock
        mock_response = MagicMock()
        mock_response.json.return_value = self.agent_card
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Call the method
        result = self.client.discover_agent()
        
        # Assertions
        mock_get.assert_called_once_with(f"{self.server_url}/.well-known/agent.json")
        self.assertEqual(result, self.agent_card)
        self.assertEqual(self.client.agent_card, self.agent_card)
    
    @patch('requests.post')
    def test_send_task(self, mock_post):
        """Test sending a task to the A2A server."""
        # Configure the mock
        mock_response = MagicMock()
        mock_response.json.return_value = self.task_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test data
        message_text = "Analyze BTC market"
        task_id = self.task_response["task_id"]
        
        # Call with explicit task_id
        result = self.client.send_task(message_text, task_id)
        
        # Assertions
        mock_post.assert_called_once()
        self.assertEqual(result, self.task_response)
        
        # Verify the JSON payload sent to the server
        call_args = mock_post.call_args
        url = call_args[0][0]
        json_data = call_args[1]['json']
        
        self.assertEqual(url, f"{self.server_url}/api/v1/tasks/send")
        self.assertEqual(json_data["task_id"], task_id)
        self.assertEqual(json_data["message"]["role"], "user")
        self.assertEqual(len(json_data["message"]["parts"]), 1)
        self.assertEqual(json_data["message"]["parts"][0]["type"], "text")
        self.assertEqual(json_data["message"]["parts"][0]["text"], message_text)
    
    @patch('requests.post')
    def test_send_task_generates_uuid(self, mock_post):
        """Test that send_task generates a UUID when task_id is not provided."""
        # Configure the mock
        mock_response = MagicMock()
        mock_response.json.return_value = self.task_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Call without task_id
        result = self.client.send_task("Analyze BTC market")
        
        # Assertions
        self.assertEqual(result, self.task_response)
        
        # Verify a UUID was generated
        call_args = mock_post.call_args
        json_data = call_args[1]['json']
        
        # Verify UUID format - should not raise ValueError
        uuid.UUID(json_data["task_id"])
    
    @patch('requests.get')
    def test_get_task(self, mock_get):
        """Test retrieving a task's status."""
        # Configure the mock
        mock_response = MagicMock()
        mock_response.json.return_value = self.task_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test data
        task_id = self.task_response["task_id"]
        
        # Call the method
        result = self.client.get_task(task_id)
        
        # Assertions
        mock_get.assert_called_once_with(f"{self.server_url}/api/v1/tasks/{task_id}")
        self.assertEqual(result, self.task_response)
    
    @patch('requests.delete')
    def test_cancel_task(self, mock_delete):
        """Test canceling a task."""
        # Configure the mock
        mock_response = MagicMock()
        mock_response.json.return_value = {"task_id": self.task_response["task_id"], "status": "canceled"}
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response
        
        # Test data
        task_id = self.task_response["task_id"]
        
        # Call the method
        result = self.client.cancel_task(task_id)
        
        # Assertions
        mock_delete.assert_called_once_with(f"{self.server_url}/api/v1/tasks/{task_id}")
        self.assertEqual(result["status"], "canceled")
        self.assertEqual(result["task_id"], task_id)
    
    def test_get_latest_agent_message(self):
        """Test extracting the latest agent message from a task."""
        # Call the method
        result = self.client.get_latest_agent_message(self.task_response)
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result["role"], "agent")
        self.assertEqual(result["parts"][0]["text"], 
                         "BTC is showing a bullish trend with strong support at $65,000.")
    
    def test_get_latest_agent_message_no_messages(self):
        """Test handling when there are no agent messages."""
        # Create a task with no agent messages
        task = {
            "task_id": str(uuid.uuid4()),
            "status": "submitted",
            "messages": [
                {
                    "role": "user",
                    "parts": [{"type": "text", "text": "Hello"}]
                }
            ]
        }
        
        # Call the method
        result = self.client.get_latest_agent_message(task)
        
        # Assertions
        self.assertIsNone(result)
    
    def test_get_all_artifacts(self):
        """Test extracting artifacts from a task."""
        # Call the method
        result = self.client.get_all_artifacts(self.task_response)
        
        # Assertions
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], "crypto_chart")
        self.assertEqual(result[0]["display_name"], "BTC Price Chart")
    
    @patch('requests.get')
    @patch('requests.post')
    def test_execute_skill(self, mock_post, mock_get):
        """Test executing a specific skill on the agent."""
        # Configure the discover_agent mock
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = self.agent_card
        mock_get_response.raise_for_status.return_value = None
        mock_get.return_value = mock_get_response
        
        # Configure the send_task mock
        mock_post_response = MagicMock()
        mock_post_response.json.return_value = {**self.task_response, "status": "completed"}
        mock_post_response.raise_for_status.return_value = None
        mock_post.return_value = mock_post_response
        
        # Test data
        skill_name = "market_analysis"
        skill_inputs = {"assets": ["BTC", "ETH"]}
        
        # Call the method with wait_for_completion=False to avoid mocking get_task in a loop
        result = self.client.execute_skill(skill_name, skill_inputs, wait_for_completion=False)
        
        # Assertions
        mock_get.assert_called_once_with(f"{self.server_url}/.well-known/agent.json")
        mock_post.assert_called_once()
        
        # Verify the JSON payload
        call_args = mock_post.call_args
        json_data = call_args[1]['json']
        
        self.assertEqual(json_data["message"]["parts"][0]["type"], "text")
        self.assertEqual(json_data["message"]["parts"][0]["text"], f"Execute skill: {skill_name}")
        self.assertEqual(json_data["message"]["parts"][1]["type"], "data")
        self.assertEqual(json_data["message"]["parts"][1]["data"]["skill"], skill_name)
        self.assertEqual(json_data["message"]["parts"][1]["data"]["inputs"], skill_inputs)
    
    @patch('requests.get')
    def test_execute_skill_invalid_skill(self, mock_get):
        """Test that an error is raised when executing an invalid skill."""
        # Configure the discover_agent mock
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = self.agent_card
        mock_get_response.raise_for_status.return_value = None
        mock_get.return_value = mock_get_response
        
        # Set agent_card
        self.client.agent_card = self.agent_card
        
        # Test with invalid skill
        with self.assertRaises(ValueError) as context:
            self.client.execute_skill("invalid_skill", {})
        
        self.assertIn("not found in agent capabilities", str(context.exception))
    
    @patch('requests.post')
    def test_send_task_error_handling(self, mock_post):
        """Test error handling when sending a task."""
        # Configure the mock to raise an exception
        mock_post.side_effect = requests.RequestException("Connection error")
        
        # Test
        with self.assertRaises(requests.RequestException):
            self.client.send_task("Test message")


if __name__ == '__main__':
    unittest.main() 