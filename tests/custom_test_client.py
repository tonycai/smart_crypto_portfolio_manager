"""
Custom Test Client for ASGI applications

This module provides a custom test client that is compatible with newer versions
of httpx and FastAPI/Starlette for testing ASGI applications.
"""
import json
import httpx
from typing import Any, Dict, Mapping, Optional, Union


class CustomTestClient:
    """
    A custom test client for ASGI applications that wraps httpx.ASGITransport
    to provide a compatible interface with older versions of TestClient.
    """
    
    def __init__(self, app):
        """
        Initialize the client with an ASGI application.
        
        Args:
            app: An ASGI application
        """
        self.app = app
        self._client = httpx.AsyncClient(
            base_url="http://testserver", 
            transport=httpx.ASGITransport(app=app)
        )
    
    def get(self, url: str, **kwargs):
        """
        Perform a GET request.
        
        Args:
            url: The URL to request
            **kwargs: Additional arguments to pass to httpx
            
        Returns:
            A Response object
        """
        return httpx.get(
            url, 
            base_url="http://testserver",
            transport=httpx.ASGITransport(app=self.app),
            **kwargs
        )
    
    def post(self, url: str, json: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Perform a POST request.
        
        Args:
            url: The URL to request
            json: The JSON data to send
            **kwargs: Additional arguments to pass to httpx
            
        Returns:
            A Response object
        """
        return httpx.post(
            url,
            json=json,
            base_url="http://testserver",
            transport=httpx.ASGITransport(app=self.app),
            **kwargs
        )
    
    def put(self, url: str, json: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Perform a PUT request.
        
        Args:
            url: The URL to request
            json: The JSON data to send
            **kwargs: Additional arguments to pass to httpx
            
        Returns:
            A Response object
        """
        return httpx.put(
            url,
            json=json,
            base_url="http://testserver",
            transport=httpx.ASGITransport(app=self.app),
            **kwargs
        )
    
    def delete(self, url: str, **kwargs):
        """
        Perform a DELETE request.
        
        Args:
            url: The URL to request
            **kwargs: Additional arguments to pass to httpx
            
        Returns:
            A Response object
        """
        return httpx.delete(
            url,
            base_url="http://testserver",
            transport=httpx.ASGITransport(app=self.app),
            **kwargs
        ) 