"""
A2A Server Implementation for Smart Crypto Portfolio Manager

This module implements Google's Agent-to-Agent (A2A) protocol server endpoints,
allowing other agents to communicate with our crypto trading agents.
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Smart Crypto Portfolio Manager A2A API")

# In-memory database for tasks (in production, use a proper database)
tasks_db = {}


# A2A Models based on A2A protocol specification
class TaskMessage(BaseModel):
    role: str
    parts: List[Dict]
    name: Optional[str] = None


class TaskRequest(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: TaskMessage


class TaskStatusUpdateEvent(BaseModel):
    type: str = "status"
    status: str
    update_time: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class TaskResponse(BaseModel):
    task_id: str
    status: str
    messages: List[TaskMessage] = []
    artifacts: List[Dict] = []
    created_time: str
    updated_time: str


# Routes for A2A protocol endpoints
@app.get("/.well-known/agent.json")
async def agent_card():
    """Return the Agent Card following A2A protocol."""
    try:
        with open(".well-known/agent.json", "r") as f:
            agent_card_data = json.load(f)
        return JSONResponse(content=agent_card_data)
    except Exception as e:
        logger.error(f"Error serving agent card: {e}")
        raise HTTPException(status_code=500, detail="Error serving agent card")


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


# Helper functions
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
                        {"date": "2023-06-02", "price": 66800},
                        {"date": "2023-06-03", "price": 67500},
                        {"date": "2023-06-04", "price": 66900},
                        {"date": "2023-06-05", "price": 67200},
                        {"date": "2023-06-06", "price": 68100},
                        {"date": "2023-06-07", "price": 67800}
                    ]
                }
            }
        ]
    }
    tasks_db[task_id]["artifacts"].append(artifact)


def handle_trade_execution(task_id: str, user_text: str):
    """Handle trade execution requests."""
    # Simulate trade execution result
    response_text = """
    # Trade Execution
    
    I've analyzed your trade request:
    
    - Order Type: MARKET
    - Asset: BTC
    - Side: BUY
    - Amount: $1,000
    
    The order has been successfully executed:
    - Filled at: $67,842.50
    - Amount: 0.01473 BTC
    - Fee: $1.70
    
    Your portfolio has been updated accordingly.
    """
    
    agent_response = create_agent_response(response_text)
    tasks_db[task_id]["messages"].append(agent_response)
    
    # Add a trade receipt artifact
    artifact = {
        "artifact_id": str(uuid.uuid4()),
        "type": "trade_receipt",
        "mime_type": "application/json",
        "display_name": "BTC Purchase Receipt",
        "parts": [
            {
                "type": "data",
                "data": {
                    "order_id": f"ord_{uuid.uuid4().hex[:12]}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "asset": "BTC",
                    "order_type": "MARKET",
                    "side": "BUY",
                    "amount_usd": 1000.00,
                    "amount_crypto": 0.01473,
                    "price": 67842.50,
                    "fee": 1.70,
                    "status": "FILLED"
                }
            }
        ]
    }
    tasks_db[task_id]["artifacts"].append(artifact)


def handle_risk_management(task_id: str, user_text: str):
    """Handle risk management requests."""
    # Simulate risk assessment result
    response_text = """
    # Risk Assessment
    
    Current portfolio risk metrics:
    
    - Volatility Risk: MEDIUM (30-day volatility of 2.8%)
    - Concentration Risk: HIGH (72% in BTC)
    - Correlation Risk: MEDIUM (assets show moderate correlation)
    - Market Risk: LOW (positive market conditions)
    
    Recommended actions:
    1. Rebalance to reduce BTC exposure to 60%
    2. Increase stablecoin allocation to 15%
    3. Consider adding uncorrelated assets
    """
    
    agent_response = create_agent_response(response_text)
    tasks_db[task_id]["messages"].append(agent_response)
    
    # Add a risk assessment artifact
    artifact = {
        "artifact_id": str(uuid.uuid4()),
        "type": "risk_assessment",
        "mime_type": "application/json",
        "display_name": "Portfolio Risk Assessment",
        "parts": [
            {
                "type": "data",
                "data": {
                    "portfolio_id": "default-portfolio",
                    "timestamp": datetime.utcnow().isoformat(),
                    "risk_metrics": {
                        "volatility": 2.8,
                        "concentration": 72.0,
                        "var_95": 8.5,
                        "sharpe_ratio": 1.2
                    },
                    "risk_levels": {
                        "volatility": "MEDIUM",
                        "concentration": "HIGH",
                        "market": "LOW",
                        "overall": "MEDIUM"
                    },
                    "recommendations": [
                        "Rebalance to reduce BTC exposure to 60%",
                        "Increase stablecoin allocation to 15%",
                        "Consider adding uncorrelated assets"
                    ]
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
    
    Current portfolio valuation: $145,720.85
    
    Asset allocation:
    - BTC: 72% ($104,919.01)
    - ETH: 18% ($26,229.75)
    - SOL: 5% ($7,286.04)
    - USDC: 5% ($7,286.04)
    
    Performance:
    - 24h: +2.4%
    - 7d: +8.7%
    - 30d: +15.2%
    - YTD: +42.6%
    
    Top performers: SOL (+18.3%), BTC (+9.2%)
    """
    
    agent_response = create_agent_response(response_text)
    tasks_db[task_id]["messages"].append(agent_response)
    
    # Add a portfolio report artifact
    artifact = {
        "artifact_id": str(uuid.uuid4()),
        "type": "portfolio_report",
        "mime_type": "application/json",
        "display_name": "Portfolio Summary Report",
        "parts": [
            {
                "type": "data",
                "data": {
                    "portfolio_id": "default-portfolio",
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_value_usd": 145720.85,
                    "assets": [
                        {"symbol": "BTC", "amount": 1.55, "value_usd": 104919.01, "allocation": 72.0},
                        {"symbol": "ETH", "amount": 8.73, "value_usd": 26229.75, "allocation": 18.0},
                        {"symbol": "SOL", "amount": 48.6, "value_usd": 7286.04, "allocation": 5.0},
                        {"symbol": "USDC", "amount": 7286.04, "value_usd": 7286.04, "allocation": 5.0}
                    ],
                    "performance": {
                        "24h": 2.4,
                        "7d": 8.7,
                        "30d": 15.2,
                        "ytd": 42.6
                    }
                }
            }
        ]
    }
    tasks_db[task_id]["artifacts"].append(artifact)


def create_agent_response(text: str) -> Dict:
    """Create an agent response message."""
    return {
        "role": "agent",
        "parts": [
            {
                "type": "text",
                "text": text
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 