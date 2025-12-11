from fastapi import FastAPI, HTTPException
from app.api.graph_api import router as graph_router
from app.websocket_api import router as websocket_router
from app.engine import Graph
from app.schemas import GraphRun, GraphStateResponse, GraphCreateResponse
from app.sample_agent import create_code_review_graph
from app.storage import graphs, runs, run_logs
from app.task_manager import task_manager
import uuid
from typing import Dict, Any

app = FastAPI(title="Workflow Engine", version="0.1.0")
app.include_router(graph_router)
app.include_router(websocket_router)

@app.post("/graph/create_sample", response_model=GraphCreateResponse)
async def create_sample_graph():
    """Creates the Code Review Mini-Agent graph with pre-defined logic."""
    graph = create_code_review_graph()
    graph_id = str(uuid.uuid4())
    graphs[graph_id] = graph
    return {"graph_id": graph_id}

@app.post("/graph/run", response_model=GraphStateResponse)
async def run_graph(data: GraphRun, sync: bool = False):
    """
    Start a graph execution.
    - If sync=false (default): starts in background and returns immediately with status 'running'.
    - If sync=true: runs synchronously and returns final state + history.
    """
    graph = graphs.get(data.graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")
    
    if sync:
        # Run synchronously and return final state
        run_id = str(uuid.uuid4())
        result = graph.run(data.initial_state)
        runs[run_id] = {
            "status": "completed",
            "state": result.get("final_state", {}),
            "history": result.get("history", [])
        }
        return {
            "run_id": run_id,
            "status": "completed",
            "state": result.get("final_state", {}),
            "history": result.get("history", [])
        }
    else:
        # Start execution in background and return immediately
        run_id = task_manager.start_execution(graph, data.initial_state)
        return {
            "run_id": run_id, 
            "status": "running", 
            "state": data.initial_state,
            "history": []
        }

@app.get("/graph/state/{run_id}", response_model=GraphStateResponse)
async def get_run_state(run_id: str):
    """Get the current state and logs of a workflow run."""
    run_data = runs.get(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail="Run not found")
    
    response = {
        "run_id": run_id,
        "status": run_data["status"],
        "state": run_data.get("state", {}),
        "history": run_data.get("history", [])
    }
    
    return response
