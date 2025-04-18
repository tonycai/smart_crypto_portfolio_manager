"""
A2A Server Implementation for Smart Crypto Portfolio Manager

This module implements Google's Agent-to-Agent (A2A) protocol server endpoints,
allowing other agents to communicate with our crypto trading agents.
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Awaitable

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# A2A Models based on A2A protocol specification
class MessagePart(BaseModel):
    """A part of a message in the A2A protocol."""
    type: str
    content: Any


class Message(BaseModel):
    """A message in the A2A protocol."""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    from_agent: str
    to_agent: str
    content: Dict
    parts: List[MessagePart] = []
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Task(BaseModel):
    """A task in the A2A protocol."""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    capability: str
    parameters: Dict
    status: str = "pending"
    priority: str = "normal"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    result: Optional[Dict] = None
    messages: List[Message] = []


class TaskMessage(BaseModel):
    """User message for a task in the A2A protocol."""
    role: str
    parts: List[Dict]
    name: Optional[str] = None


class TaskRequest(BaseModel):
    """Request for creating a task in the A2A protocol."""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: TaskMessage


class TaskStatusUpdateEvent(BaseModel):
    """Event for updating task status in the A2A protocol."""
    type: str = "status"
    status: str
    update_time: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class TaskResponse(BaseModel):
    """Response for a task in the A2A protocol."""
    task_id: str
    status: str
    messages: List[TaskMessage] = []
    artifacts: List[Dict] = []
    created_time: str
    updated_time: str


class A2AServer:
    """A2A Protocol Server Implementation"""
    
    def __init__(self, agent_card_path: str):
        """Initialize the A2A server with agent card path."""
        self.agent_card_path = agent_card_path
        self.tasks = {}  # In-memory task storage
        self.capability_handlers = {}  # Registered capability handlers
        self.app = self._create_app()
        
    def _create_app(self) -> FastAPI:
        """Create and configure the FastAPI application."""
        app = FastAPI(title="Smart Crypto Portfolio Manager A2A API")
        
        @app.get("/")
        async def root():
            """Root endpoint providing basic agent information."""
            return {
                "name": self._get_agent_name(),
                "version": self._get_agent_version(),
                "status": "online",
                "capabilities": list(self.capability_handlers.keys()),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @app.get("/api/v1/agent")
        async def get_agent_card():
            """Return the agent card."""
            try:
                with open(self.agent_card_path, "r") as f:
                    agent_card_data = json.load(f)
                return JSONResponse(content=agent_card_data)
            except Exception as e:
                logger.error(f"Error serving agent card: {e}")
                raise HTTPException(status_code=500, detail="Error serving agent card")
        
        @app.post("/api/v1/tasks", status_code=201)
        async def create_task(task_data: dict, background_tasks: BackgroundTasks):
            """Create a new task."""
            if "capability" not in task_data:
                raise HTTPException(status_code=400, detail="Capability is required")
                
            capability = task_data["capability"]
            if capability not in self.capability_handlers:
                raise HTTPException(status_code=400, detail=f"Capability {capability} is not supported")
            
            task = Task(
                capability=capability,
                parameters=task_data.get("parameters", {}),
                priority=task_data.get("priority", "normal")
            )
            
            self.tasks[task.task_id] = task
            
            # Process task in background
            background_tasks.add_task(self._process_task, task.task_id)
            
            return task
        
        @app.get("/api/v1/tasks/{task_id}")
        async def get_task(task_id: str):
            """Get a task by ID."""
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            
            return self.tasks[task_id]
        
        @app.put("/api/v1/tasks/{task_id}")
        async def update_task(task_id: str, update_data: dict):
            """Update a task."""
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            
            task = self.tasks[task_id]
            
            # Update allowed fields
            if "status" in update_data:
                task.status = update_data["status"]
            
            if "result" in update_data:
                task.result = update_data["result"]
            
            task.updated_at = datetime.utcnow().isoformat()
            
            return task
        
        @app.delete("/api/v1/tasks/{task_id}")
        async def cancel_task(task_id: str):
            """Cancel a task."""
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            
            task = self.tasks[task_id]
            task.status = "canceled"
            task.updated_at = datetime.utcnow().isoformat()
            
            return {"message": f"Task {task_id} canceled successfully"}
        
        @app.post("/api/v1/tasks/{task_id}/messages", status_code=201)
        async def send_message(task_id: str, message_data: dict):
            """Send a message for a task."""
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            
            message = Message(
                task_id=task_id,
                **message_data
            )
            
            self.tasks[task_id].messages.append(message)
            
            return message
        
        @app.get("/api/v1/tasks/{task_id}/messages")
        async def get_messages(task_id: str):
            """Get all messages for a task."""
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            
            return self.tasks[task_id].messages
        
        # LEGACY A2A PROTOCOL ROUTES
        
        @app.get("/.well-known/agent.json")
        async def agent_card():
            """Return the Agent Card following A2A protocol."""
            return await get_agent_card()
        
        @app.post("/api/v1/tasks/send")
        async def tasks_send(task_request: TaskRequest, background_tasks: BackgroundTasks):
            """
            Implement the A2A tasks/send endpoint.
            This endpoint receives a task and user message, processes it, and returns the result.
            """
            task_id = task_request.task_id
            user_message = task_request.message
            
            # Create a new task if it doesn't exist
            if task_id not in tasks_db:
                tasks_db[task_id] = {
                    "task_id": task_id,
                    "status": "submitted",
                    "messages": [user_message.dict()],
                    "artifacts": [],
                    "created_time": datetime.utcnow().isoformat(),
                    "updated_time": datetime.utcnow().isoformat()
                }
            else:
                # Update existing task with new message
                tasks_db[task_id]["messages"].append(user_message.dict())
                tasks_db[task_id]["updated_time"] = datetime.utcnow().isoformat()
                tasks_db[task_id]["status"] = "working"
            
            # Process the task asynchronously
            background_tasks.add_task(process_task, task_id)
            
            # Return current task state
            return TaskResponse(**tasks_db[task_id])
        
        @app.get("/api/v1/tasks/{task_id}")
        async def tasks_get(task_id: str):
            """
            Implement the A2A tasks/get endpoint.
            This endpoint returns the current state of a task.
            """
            if task_id not in tasks_db:
                raise HTTPException(status_code=404, detail="Task not found")
            
            return TaskResponse(**tasks_db[task_id])
        
        @app.post("/api/v1/tasks/sendSubscribe")
        async def tasks_send_subscribe(task_request: TaskRequest):
            """
            Implement the A2A tasks/sendSubscribe endpoint.
            This endpoint receives a task and streams updates as Server-Sent Events.
            """
            task_id = task_request.task_id
            user_message = task_request.message
            
            # Create a new task if it doesn't exist
            if task_id not in tasks_db:
                tasks_db[task_id] = {
                    "task_id": task_id,
                    "status": "submitted",
                    "messages": [user_message.dict()],
                    "artifacts": [],
                    "created_time": datetime.utcnow().isoformat(),
                    "updated_time": datetime.utcnow().isoformat()
                }
            else:
                # Update existing task with new message
                tasks_db[task_id]["messages"].append(user_message.dict())
                tasks_db[task_id]["updated_time"] = datetime.utcnow().isoformat()
                tasks_db[task_id]["status"] = "working"
            
            # Stream updates
            return EventSourceResponse(task_status_generator(task_id))
        
        @app.delete("/api/v1/tasks/{task_id}")
        async def tasks_cancel(task_id: str):
            """
            Implement the A2A tasks/cancel endpoint.
            This endpoint cancels a task.
            """
            if task_id not in tasks_db:
                raise HTTPException(status_code=404, detail="Task not found")
            
            tasks_db[task_id]["status"] = "canceled"
            tasks_db[task_id]["updated_time"] = datetime.utcnow().isoformat()
            
            return {"task_id": task_id, "status": "canceled"}
        
        return app
    
    def _get_agent_name(self) -> str:
        """Get the agent name from the agent card."""
        try:
            with open(self.agent_card_path, "r") as f:
                agent_card_data = json.load(f)
            return agent_card_data.get("name", "Unknown Agent")
        except Exception:
            return "Unknown Agent"
    
    def _get_agent_version(self) -> str:
        """Get the agent version from the agent card."""
        try:
            with open(self.agent_card_path, "r") as f:
                agent_card_data = json.load(f)
            return agent_card_data.get("version", "1.0.0")
        except Exception:
            return "1.0.0"
    
    async def _process_task(self, task_id: str):
        """Process a task using the registered capability handler."""
        task = self.tasks[task_id]
        task.status = "processing"
        task.updated_at = datetime.utcnow().isoformat()
        
        try:
            handler = self.capability_handlers.get(task.capability)
            if handler:
                result = await handler(task.parameters)
                task.result = result
                task.status = "completed"
            else:
                task.status = "failed"
                task.result = {"error": f"No handler found for capability {task.capability}"}
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            task.status = "failed"
            task.result = {"error": str(e)}
        
        task.updated_at = datetime.utcnow().isoformat()
    
    def register_capability_handler(self, capability: str, handler: Callable[[Dict], Awaitable[Dict]]):
        """Register a handler for a specific capability."""
        self.capability_handlers[capability] = handler


# In-memory database for legacy tasks (in production, use a proper database)
tasks_db = {}


# Helper functions for legacy A2A protocol
async def task_status_generator(task_id: str):
    """Generate SSE events for task status updates."""
    if task_id not in tasks_db:
        yield {"data": json.dumps({"error": "Task not found"})}
        return
    
    # Initial status
    status_update = TaskStatusUpdateEvent(status=tasks_db[task_id]["status"])
    yield {"data": status_update.json()}
    
    # Start processing task in background
    process_task(task_id)
    
    # Yield final status
    status_update = TaskStatusUpdateEvent(status=tasks_db[task_id]["status"])
    yield {"data": status_update.json()}


def process_task(task_id: str):
    """Process a task and update its status."""
    try:
        # Update status to working
        tasks_db[task_id]["status"] = "working"
        tasks_db[task_id]["updated_time"] = datetime.utcnow().isoformat()
        
        # Get the latest user message
        latest_message = tasks_db[task_id]["messages"][-1]
        
        # Simple dispatch based on user input
        if latest_message["role"] == "user":
            message_parts = [part for part in latest_message["parts"] if part.get("type") == "text"]
            user_text = message_parts[0]["text"] if message_parts else ""
            
            # Route to appropriate agent based on content
            if "market analysis" in user_text.lower():
                handle_market_analysis(task_id, user_text)
            elif "trade" in user_text.lower() or "buy" in user_text.lower() or "sell" in user_text.lower():
                handle_trade_execution(task_id, user_text)
            elif "risk" in user_text.lower():
                handle_risk_management(task_id, user_text)
            elif "report" in user_text.lower() or "portfolio" in user_text.lower():
                handle_portfolio_reporting(task_id, user_text)
            else:
                # Default response
                agent_response = create_agent_response("I'm not sure how to help with that. You can ask about market analysis, trading, risk management, or portfolio reporting.")
                tasks_db[task_id]["messages"].append(agent_response)
        
        # Set status to completed
        tasks_db[task_id]["status"] = "completed"
        tasks_db[task_id]["updated_time"] = datetime.utcnow().isoformat()
        
    except Exception as e:
        logger.error(f"Error processing task {task_id}: {e}")
        tasks_db[task_id]["status"] = "failed"
        tasks_db[task_id]["updated_time"] = datetime.utcnow().isoformat()
        
        # Add error message
        error_response = create_agent_response(f"An error occurred: {str(e)}")
        tasks_db[task_id]["messages"].append(error_response)


def handle_market_analysis(task_id: str, user_text: str):
    """Handle market analysis requests."""
    # Simulate market analysis result
    response_text = """
    # Market Analysis
    
    Based on current market conditions:
    
    - BTC: Bullish trend detected, RSI at 62, potential resistance at $68,000
    - ETH: Neutral trend, forming a consolidation pattern
    - SOL: Strong momentum, potential breakout above $150
    
    Overall market sentiment is positive with moderate volatility expected.
    """
    
    agent_response = create_agent_response(response_text)
    tasks_db[task_id]["messages"].append(agent_response)
    
    # Add a chart artifact
    artifact = {
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
                        {"date": "2023-06-02", "price": 65800},
                        {"date": "2023-06-03", "price": 66500},
                        {"date": "2023-06-04", "price": 67200},
                        {"date": "2023-06-05", "price": 66800},
                        {"date": "2023-06-06", "price": 67500},
                        {"date": "2023-06-07", "price": 68000}
                    ]
                }
            }
        ]
    }
    
    tasks_db[task_id]["artifacts"].append(artifact)


def handle_trade_execution(task_id: str, user_text: str):
    """Handle trade execution requests."""
    # Simulate trade execution
    
    # Extract trade details from user text
    import re
    
    # Try to extract trade parameters from user text
    buy_match = re.search(r'buy\s+(\d+)\s+([A-Za-z]{3,})', user_text.lower())
    sell_match = re.search(r'sell\s+(\d+)\s+([A-Za-z]{3,})', user_text.lower())
    
    if buy_match:
        amount = buy_match.group(1)
        asset = buy_match.group(2).upper()
        trade_type = "buy"
    elif sell_match:
        amount = sell_match.group(1)
        asset = sell_match.group(2).upper()
        trade_type = "sell"
    else:
        # Default to a BTC buy if no specific instruction
        amount = "0.1"
        asset = "BTC"
        trade_type = "buy"
    
    # Simulate order execution
    order_id = str(uuid.uuid4())
    price = {
        "BTC": 67500,
        "ETH": 3200,
        "SOL": 145,
        "ADA": 0.5,
        "DOT": 7.2
    }.get(asset, 100)  # Default price for unknown assets
    
    response_text = f"""
    # Trade Execution Confirmed
    
    Your {trade_type} order for {amount} {asset} has been executed:
    
    - Order ID: {order_id[:8]}
    - Type: {trade_type.upper()}
    - Asset: {asset}
    - Amount: {amount}
    - Price: ${price}
    - Total: ${float(amount) * price}
    - Status: COMPLETED
    - Timestamp: {datetime.utcnow().isoformat()}
    
    The order has been added to your portfolio.
    """
    
    agent_response = create_agent_response(response_text)
    tasks_db[task_id]["messages"].append(agent_response)
    
    # Add trade receipt artifact
    artifact = {
        "artifact_id": str(uuid.uuid4()),
        "type": "trade_receipt",
        "mime_type": "application/json",
        "display_name": f"{trade_type.capitalize()} {amount} {asset} Receipt",
        "parts": [
            {
                "type": "data",
                "data": {
                    "order_id": order_id,
                    "type": trade_type,
                    "asset": asset,
                    "amount": float(amount),
                    "price": price,
                    "total": float(amount) * price,
                    "status": "COMPLETED",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        ]
    }
    
    tasks_db[task_id]["artifacts"].append(artifact)


def handle_risk_management(task_id: str, user_text: str):
    """Handle risk management requests."""
    # Simulate risk assessment
    
    # Extract asset from user text if available
    import re
    
    asset_match = re.search(r'risk\s+(?:for|of)\s+([A-Za-z]{3,})', user_text.lower())
    if asset_match:
        asset = asset_match.group(1).upper()
    else:
        # Default to portfolio-wide risk assessment
        asset = "PORTFOLIO"
    
    if asset == "PORTFOLIO":
        response_text = """
        # Portfolio Risk Assessment
        
        Current portfolio risk metrics:
        
        - Value at Risk (VaR, 95%): 3.8%
        - Maximum Drawdown: 15.2%
        - Sharpe Ratio: 1.8
        - Volatility (30d): 2.6%
        
        Risk level: **MODERATE**
        
        Recommendations:
        - Consider diversifying into stablecoins to reduce overall volatility
        - Current BTC allocation (65%) exceeds recommended maximum (50%)
        - Consider setting stop-loss orders for high-volatility assets
        """
    else:
        # Asset-specific risk assessment
        risk_profiles = {
            "BTC": {
                "var": 4.2,
                "volatility": 3.1,
                "risk_level": "MODERATE-HIGH",
                "recommendation": "Consider reducing position size or setting stop-loss orders"
            },
            "ETH": {
                "var": 3.9,
                "volatility": 2.8,
                "risk_level": "MODERATE",
                "recommendation": "Current position size is within acceptable risk parameters"
            },
            "SOL": {
                "var": 6.5,
                "volatility": 5.2,
                "risk_level": "HIGH",
                "recommendation": "Reduce position size to less than 5% of portfolio"
            }
        }
        
        profile = risk_profiles.get(asset, {
            "var": 5.0,
            "volatility": 4.0,
            "risk_level": "UNKNOWN",
            "recommendation": "Insufficient data for specific recommendations"
        })
        
        response_text = f"""
        # Risk Assessment for {asset}
        
        Risk metrics:
        
        - Value at Risk (VaR, 95%): {profile["var"]}%
        - Volatility (30d): {profile["volatility"]}%
        - Risk level: **{profile["risk_level"]}**
        
        Recommendation:
        {profile["recommendation"]}
        """
    
    agent_response = create_agent_response(response_text)
    tasks_db[task_id]["messages"].append(agent_response)
    
    # Add risk report artifact
    artifact = {
        "artifact_id": str(uuid.uuid4()),
        "type": "risk_report",
        "mime_type": "application/json",
        "display_name": f"Risk Report for {asset}",
        "parts": [
            {
                "type": "data",
                "data": {
                    "asset": asset,
                    "timestamp": datetime.utcnow().isoformat(),
                    "metrics": {
                        "var_95": 3.8 if asset == "PORTFOLIO" else 4.2,
                        "volatility": 2.6 if asset == "PORTFOLIO" else 3.1,
                        "risk_level": "MODERATE" if asset == "PORTFOLIO" else "MODERATE-HIGH"
                    }
                }
            }
        ]
    }
    
    tasks_db[task_id]["artifacts"].append(artifact)


def handle_portfolio_reporting(task_id: str, user_text: str):
    """Handle portfolio reporting requests."""
    # Simulate portfolio report
    
    response_text = """
    # Portfolio Summary
    
    Current portfolio value: $125,432.78
    24h change: +2.3% (+$2,821.15)
    
    Asset allocation:
    - BTC: 65% ($81,531.31)
    - ETH: 20% ($25,086.56)
    - SOL: 10% ($12,543.28)
    - USDC: 5% ($6,271.64)
    
    Performance:
    - 7d: +5.2%
    - 30d: +12.8%
    - YTD: +32.5%
    
    Top performer: SOL (+18.3% this month)
    Worst performer: USDC (0% this month)
    """
    
    agent_response = create_agent_response(response_text)
    tasks_db[task_id]["messages"].append(agent_response)
    
    # Add portfolio report artifact
    artifact = {
        "artifact_id": str(uuid.uuid4()),
        "type": "portfolio_report",
        "mime_type": "application/json",
        "display_name": "Portfolio Summary Report",
        "parts": [
            {
                "type": "data",
                "data": {
                    "total_value": 125432.78,
                    "change_24h": 2.3,
                    "change_24h_value": 2821.15,
                    "allocation": [
                        {"asset": "BTC", "percentage": 65, "value": 81531.31},
                        {"asset": "ETH", "percentage": 20, "value": 25086.56},
                        {"asset": "SOL", "percentage": 10, "value": 12543.28},
                        {"asset": "USDC", "percentage": 5, "value": 6271.64}
                    ],
                    "performance": {
                        "7d": 5.2,
                        "30d": 12.8,
                        "ytd": 32.5
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        ]
    }
    
    tasks_db[task_id]["artifacts"].append(artifact)


def create_agent_response(text: str) -> Dict:
    """Create a standard agent response message."""
    return {
        "role": "assistant",
        "parts": [
            {
                "type": "text",
                "text": text
            }
        ]
    }


def create_a2a_server(agent_card_path: str) -> A2AServer:
    """Factory function to create an A2A server instance."""
    return A2AServer(agent_card_path)


# Create a default FastAPI app for backward compatibility
# This allows old code to continue to import 'app' directly from this module
default_server = A2AServer(".well-known/agent.json")
app = default_server.app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 