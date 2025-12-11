from typing import Dict, Any, Callable, List, Optional
import copy
import logging
import asyncio
from datetime import datetime

# Simple logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

State = Dict[str, Any]

class Node:
    def __init__(self, name: str, func: Callable[[State], State]):
        self.name = name
        self.func = func

    def run(self, state: State) -> State:
        """Executes the node function safetly, catching all exceptions."""
        try:
            return self.func(state)
        except Exception as e:
            logger.error(f"CRITICAL: Error executing node '{self.name}': {e}")
            # Return safe fallback output so the graph can continue (or at least fail gracefully)
            return {
                "error": str(e),
                "failed_node": self.name,
                "status": "node_execution_failed"
            }

class Edge:
    def __init__(self, from_node: str, to_node: str, condition: Optional[Callable[[State], bool]] = None):
        self.from_node = from_node
        self.to_node = to_node
        self.condition = condition

class Graph:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, List[Edge]] = {}  # from_node -> [Edge]
        self.entry_point: Optional[str] = None

    def add_node(self, name: str, func: Callable[[State], State]):
        self.nodes[name] = Node(name, func)
        if name not in self.edges:
            self.edges[name] = []

    def set_entry_point(self, node_name: str):
        # We allow setting entry point even if node doesn't exist yet (though create logic handles this)
        if node_name not in self.nodes:
             # This should be caught by create logic, but for safety:
             logger.warning(f"Setting entry point to non-existent node '{node_name}'.")
        self.entry_point = node_name

    def add_edge(self, from_node: str, to_node: str, condition: Optional[Callable[[State], bool]] = None):
        # Allow adding edges even if nodes technically aren't there yet (though strict create logic usually does validation)
        # But for robustness, we just ensure the list exists.
        if from_node not in self.edges:
            self.edges[from_node] = []
        
        self.edges[from_node].append(Edge(from_node, to_node, condition))

    def run(self, initial_state: State) -> Dict[str, Any]:
        """Runs the graph from the entry point with safety caps."""
        state = copy.deepcopy(initial_state)
        current_node_name = self.entry_point
        history = []
        
        steps = 0
        MAX_STEPS = 50 

        if not current_node_name or current_node_name not in self.nodes:
             return {
                 "final_state": state, 
                 "history": [], 
                 "error": "Graph entry point invalid or missing."
             }

        logger.info(f"Starting graph execution at {current_node_name}")

        while current_node_name is not None and steps < MAX_STEPS:
            steps += 1
            node = self.nodes.get(current_node_name)
            
            if not node:
                logger.error(f"Node '{current_node_name}' defined in edge but missing in nodes. Stopping.")
                history.append({"error": f"Node {current_node_name} missing"})
                break

            logger.info(f"Step {steps}: Executing {current_node_name}")
            
            # Execute node safely
            updates = node.run(state)
            
            if isinstance(updates, dict):
                state.update(updates)
            
            history.append({
                "step": steps, 
                "node": current_node_name, 
                "state_snapshot": copy.deepcopy(state)
            })

            # Transition logic
            next_node_name = None
            relevant_edges = self.edges.get(current_node_name, [])
            
            for edge in relevant_edges:
                # We catch errors in condition evaluation too
                try:
                    if edge.condition:
                        if edge.condition(state):
                            next_node_name = edge.to_node
                            logger.info(f"  Condition met for edge to {next_node_name}")
                            break
                    else:
                        # Unconditional edge
                        next_node_name = edge.to_node
                        logger.info(f"  Following unconditional edge to {next_node_name}")
                        break
                except Exception as e:
                    logger.error(f"Error evaluating edge condition from {current_node_name}: {e}")
                    # If condition fails, we treat it as False and continue to next edge
                    continue
            
            current_node_name = next_node_name
        
        if steps >= MAX_STEPS:
            logger.warning("Max steps reached, stopping execution.")
            state["_warning"] = "Max steps reached"

        return {"final_state": state, "history": history}

    async def run_async(self, initial_state: State, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Async version of run with callback support for streaming logs."""
        state = copy.deepcopy(initial_state)
        current_node_name = self.entry_point
        history = []
        
        steps = 0
        MAX_STEPS = 50

        async def emit_event(event_type: str, data: Dict[str, Any]):
            """Helper to emit events via callback."""
            if callback:
                event = {
                    "type": event_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": data
                }
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)

        if not current_node_name or current_node_name not in self.nodes:
            await emit_event("execution_failed", {
                "error": "Graph entry point invalid or missing.",
                "state": state
            })
            return {
                "final_state": state, 
                "history": [], 
                "error": "Graph entry point invalid or missing."
            }

        logger.info(f"Starting graph execution at {current_node_name}")
        await emit_event("execution_started", {
            "entry_point": current_node_name,
            "initial_state": state
        })

        while current_node_name is not None and steps < MAX_STEPS:
            steps += 1
            node = self.nodes.get(current_node_name)
            
            if not node:
                logger.error(f"Node '{current_node_name}' defined in edge but missing in nodes. Stopping.")
                await emit_event("execution_failed", {
                    "error": f"Node {current_node_name} missing",
                    "state": state
                })
                history.append({"error": f"Node {current_node_name} missing"})
                break

            logger.info(f"Step {steps}: Executing {current_node_name}")
            await emit_event("step_start", {
                "step": steps,
                "node": current_node_name,
                "state": copy.deepcopy(state)
            })
            
            # Execute node safely (we can add await here if nodes become async in future)
            updates = node.run(state)
            
            if isinstance(updates, dict):
                state.update(updates)
            
            history.append({
                "step": steps, 
                "node": current_node_name, 
                "state_snapshot": copy.deepcopy(state)
            })

            await emit_event("step_complete", {
                "step": steps,
                "node": current_node_name,
                "state": copy.deepcopy(state),
                "updates": updates if isinstance(updates, dict) else {}
            })

            # Transition logic
            next_node_name = None
            relevant_edges = self.edges.get(current_node_name, [])
            
            for edge in relevant_edges:
                try:
                    if edge.condition:
                        if edge.condition(state):
                            next_node_name = edge.to_node
                            logger.info(f"  Condition met for edge to {next_node_name}")
                            await emit_event("transition", {
                                "from_node": current_node_name,
                                "to_node": next_node_name,
                                "condition_met": True
                            })
                            break
                    else:
                        # Unconditional edge
                        next_node_name = edge.to_node
                        logger.info(f"  Following unconditional edge to {next_node_name}")
                        await emit_event("transition", {
                            "from_node": current_node_name,
                            "to_node": next_node_name,
                            "condition_met": None
                        })
                        break
                except Exception as e:
                    logger.error(f"Error evaluating edge condition from {current_node_name}: {e}")
                    continue
            
            current_node_name = next_node_name
            
            # Small delay to make streaming visible in demo
            await asyncio.sleep(0.1)
        
        if steps >= MAX_STEPS:
            logger.warning("Max steps reached, stopping execution.")
            state["_warning"] = "Max steps reached"

        await emit_event("execution_complete", {
            "final_state": state,
            "total_steps": steps,
            "history": history
        })

        return {"final_state": state, "history": history}

