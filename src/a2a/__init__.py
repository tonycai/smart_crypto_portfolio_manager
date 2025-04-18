"""
Agent-to-Agent (A2A) Protocol Implementation

This package provides client and server implementations for Google's A2A protocol,
enabling standardized communication between our crypto trading agents and other
A2A-compatible agents.
"""

from src.a2a.client import A2AClient
from src.a2a.server import app as a2a_server_app

__all__ = ['A2AClient', 'a2a_server_app'] 