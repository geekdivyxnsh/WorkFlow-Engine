from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class NodeBase(BaseModel):
    name: str
    tool_name: str  # References a function in the registry

class EdgeBase(BaseModel):
    from_node: str
    to_node: str
    condition_rule: Optional[str] = None # Simple rule expression e.g. "complexity_score > 5"

class GraphCreate(BaseModel):
    nodes: Dict[str, str]  # name -> tool_name
    edges: Dict[str, str]  # from_node -> to_node
    start: str             # entry_point node name

class GraphRun(BaseModel):
    graph_id: str
    initial_state: Dict[str, Any]

class GraphStateResponse(BaseModel):
    run_id: str
    status: str # "running", "completed", "failed"
    state: Dict[str, Any]
    history: List[Dict[str, Any]]

class GraphCreateResponse(BaseModel):
    graph_id: str
