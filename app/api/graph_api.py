from fastapi import APIRouter, Body, HTTPException
from typing import Dict
import uuid
from app.engine import Graph
from app.registry import default_registry
from app.storage import graphs
from app.schemas import GraphCreateResponse
from pydantic import BaseModel, Field

router = APIRouter()

class GraphCreate(BaseModel):
    start: str = Field(..., description="Name of the start node")
    nodes: Dict[str, str] = Field(
        ...,
        description="Mapping node_name -> tool_name (or function identifier)"
    )
    edges: Dict[str, str] = Field(
        ...,
        description="Mapping node_name -> next_node_name or expression"
    )

# Example payload to show in Swagger /docs
example_payload = {
    "start": "extract",
    "nodes": {
        "extract": "extract_tool",
        "complexity": "complexity_tool"
    },
    "edges": {
        "extract": "complexity"
    }
}

@router.post("/graph/create", response_model=GraphCreateResponse, status_code=200)
def create_graph(payload: GraphCreate = Body(..., example=example_payload)):
    """
    Create a graph:
    - start: entry node
    - nodes: mapping node_name -> tool_name
    - edges: mapping node_name -> next_node_name
    """
    graph = Graph()
    graph_id = str(uuid.uuid4())
    
    # Add nodes
    # With SmartToolRegistry, this NEVER fails.
    for name, tool_name in payload.nodes.items():
        # This get() calls create_default_tool if missing
        func = default_registry.get(tool_name) 
        graph.add_node(name, func)
    
    # Add edges
    for from_node, to_node in payload.edges.items():
        # We assume unconditional edges for this simple API
        # We treat standard edges as unconditional
        # Ideally we'd valid 'from_node' exists, but engine handles edges loosely too
        graph.add_edge(from_node, to_node)
            
    # Set entry point
    # We must ensure the start node actually exists in the graph we just built
    if payload.start not in payload.nodes:
         # If the user specified a start node that isn't in 'nodes', 
         # we should probably just add it as a default no-op node to prevent crash?
         # Or strictly, we might need to add it.
         # Let's add it dynamically to be "bulletproof".
         safe_func = default_registry.get("noop")
         graph.add_node(payload.start, safe_func)

    graph.set_entry_point(payload.start)

    # store graph
    graphs[graph_id] = graph
    
    return {"graph_id": graph_id}
