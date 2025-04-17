import json
import os
import logging
from typing import Dict, Any, List, Optional, Union
from fastapi import FastAPI, HTTPException, Body, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import our orchestration agent
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.orchestration_agent import OrchestrationAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MCP-Server")

# Create FastAPI app
app = FastAPI(
    title="Model Calling Protocol API",
    description="API endpoints implementing the Model Calling Protocol (MCP)",
    version="1.0.0",
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the orchestration agent
orchestrator = OrchestrationAgent()

# Register some sample agents for demonstration (in a real setup these would register themselves)
@app.on_event("startup")
async def startup_event():
    orchestrator.register_agent("market_data_agent", "MarketData")
    orchestrator.register_agent("market_analysis_agent", "MarketAnalysis")
    orchestrator.register_agent("trade_strategy_agent", "TradeStrategy")
    orchestrator.register_agent("trade_execution_agent", "TradeExecution")
    orchestrator.register_agent("portfolio_agent", "Portfolio")
    orchestrator.register_agent("portfolio_optimization_agent", "PortfolioOptimization")
    logger.info("Sample agents registered")


# ---------- Pydantic models for request/response validation ----------

class Error(BaseModel):
    code: str
    message: str


class FunctionCall(BaseModel):
    function_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: Optional[int] = None


class FunctionResponse(BaseModel):
    status: str
    result: Optional[Any] = None
    error: Optional[Error] = None


class AgentStatus(BaseModel):
    agent_id: str
    agent_type: str
    status: str
    last_heartbeat: str
    error_details: Optional[str] = None


class WorkflowStepStatus(BaseModel):
    step_id: str
    step_name: str
    agent_id: str
    status: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None


class WorkflowStatus(BaseModel):
    workflow_id: str
    workflow_name: str
    status: str
    steps: List[WorkflowStepStatus]
    created_at: str
    updated_at: str
    estimated_completion: Optional[str] = None


class WorkflowRequest(BaseModel):
    workflow_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class AgentRegisterRequest(BaseModel):
    agent_id: str
    agent_type: str


# ---------- API Routes ----------

@app.post("/api/v1/mcp/function", response_model=FunctionResponse, tags=["Function Execution"])
async def execute_function(function_call: FunctionCall = Body(...)):
    """
    Execute a function via the Model Calling Protocol (MCP)
    
    Args:
        function_call: The function to call with its arguments
        
    Returns:
        The function response with status and result
    """
    logger.info(f"Executing function: {function_call.function_name}")
    
    response = orchestrator.call_function(
        function_call.function_name, 
        function_call.arguments
    )
    
    if response["status"] == "error":
        return {
            "status": "error",
            "error": response["error"]
        }
    
    return response


@app.get("/api/v1/mcp/status/agents", tags=["Agent Status"])
async def get_all_agents_status():
    """
    Get the status of all agents
    
    Returns:
        A list of agent status objects and system health
    """
    response = orchestrator.get_all_agents_status()
    return response


@app.get("/api/v1/mcp/status/agent/{agent_id}", tags=["Agent Status"])
async def get_agent_status(agent_id: str = Path(...)):
    """
    Get the status of a specific agent
    
    Args:
        agent_id: The ID of the agent to query
        
    Returns:
        The agent status
    """
    response = orchestrator.get_agent_status(agent_id)
    
    if response["status"] == "error":
        raise HTTPException(
            status_code=404, 
            detail=response["error"]["message"]
        )
    
    return response


@app.post("/api/v1/mcp/agent/register", tags=["Agent Registration"])
async def register_agent(request: AgentRegisterRequest = Body(...)):
    """
    Register a new agent or update an existing one
    
    Args:
        request: The agent registration data
        
    Returns:
        Success confirmation with agent ID
    """
    response = orchestrator.register_agent(
        request.agent_id,
        request.agent_type
    )
    
    return response


@app.post("/api/v1/mcp/workflow", response_model=Dict[str, Any], tags=["Workflow"])
async def create_workflow(workflow_request: WorkflowRequest = Body(...)):
    """
    Create and execute a new workflow
    
    Args:
        workflow_request: The workflow to execute
        
    Returns:
        Workflow ID and initial status
    """
    response = orchestrator.execute_workflow(
        workflow_request.workflow_name,
        workflow_request.parameters
    )
    
    if response["status"] == "error":
        raise HTTPException(
            status_code=400, 
            detail=response["error"]["message"]
        )
    
    return response


@app.get("/api/v1/mcp/workflow/{workflow_id}", tags=["Workflow"])
async def get_workflow_status(workflow_id: str = Path(...)):
    """
    Get the status of a specific workflow
    
    Args:
        workflow_id: The ID of the workflow to query
        
    Returns:
        The workflow status
    """
    response = orchestrator.get_workflow_status(workflow_id)
    
    if response["status"] == "error":
        raise HTTPException(
            status_code=404, 
            detail=response["error"]["message"]
        )
    
    return response


# Simulates workflow progress for testing/demo purposes
@app.post("/api/v1/mcp/workflow/{workflow_id}/advance", tags=["Demo"])
async def advance_workflow(workflow_id: str = Path(...), step_index: Optional[int] = Query(None)):
    """
    [DEMO ONLY] Advance a workflow to its next step
    
    Args:
        workflow_id: The ID of the workflow to advance
        step_index: Optional specific step index to complete
        
    Returns:
        Updated workflow status
    """
    # First check if workflow exists
    status_check = orchestrator.get_workflow_status(workflow_id)
    if status_check["status"] == "error":
        raise HTTPException(
            status_code=404, 
            detail=status_check["error"]["message"]
        )
    
    # Advance the workflow
    orchestrator.simulate_workflow_progress(workflow_id, step_index)
    
    # Return updated status
    return orchestrator.get_workflow_status(workflow_id)


if __name__ == "__main__":
    import uvicorn
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=8000) 