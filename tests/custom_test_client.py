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
        self.base_url = "http://testserver"
        self.transport = httpx.ASGITransport(app=app)
    
    def get(self, url: str, **kwargs):
        """
        Perform a GET request.
        
        Args:
            url: The URL to request
            **kwargs: Additional arguments to pass to httpx
            
        Returns:
            A Response object
        """
        # Remove base_url if it's in kwargs
        kwargs.pop('base_url', None)
        
        # Build the full URL
        full_url = f"{self.base_url}{url}"
        
        # Use httpx with transport but without base_url
        return httpx.get(
            full_url,
            transport=self.transport,
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
        # Remove base_url if it's in kwargs
        kwargs.pop('base_url', None)
        
        # Build the full URL
        full_url = f"{self.base_url}{url}"
        
        # Use httpx with transport but without base_url
        return httpx.post(
            full_url,
            json=json,
            transport=self.transport,
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
        # Remove base_url if it's in kwargs
        kwargs.pop('base_url', None)
        
        # Build the full URL
        full_url = f"{self.base_url}{url}"
        
        # Use httpx with transport but without base_url
        return httpx.put(
            full_url,
            json=json,
            transport=self.transport,
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
        # Remove base_url if it's in kwargs
        kwargs.pop('base_url', None)
        
        # Build the full URL
        full_url = f"{self.base_url}{url}"
        
        # Use httpx with transport but without base_url
        return httpx.delete(
            full_url,
            transport=self.transport,
            **kwargs
        ) 