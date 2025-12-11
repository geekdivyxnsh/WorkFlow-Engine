from typing import Dict, Any, List, Set
from app.engine import Graph

# In-memory storage moved here to avoid circular imports
graphs: Dict[str, Graph] = {}
runs: Dict[str, Dict[str, Any]] = {}

# Log streaming support
run_logs: Dict[str, List[Dict[str, Any]]] = {}  # run_id -> list of log events
run_subscribers: Dict[str, Set] = {}  # run_id -> set of websocket connections
