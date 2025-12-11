from typing import Dict, Any, Optional
import asyncio
import uuid
from app.engine import Graph
from app.storage import runs, run_logs, run_subscribers
import logging

logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    """Manages background execution of workflow graphs."""
    
    def __init__(self):
        self.tasks: Dict[str, asyncio.Task] = {}
    
    async def execute_graph(
        self, 
        run_id: str, 
        graph: Graph, 
        initial_state: Dict[str, Any]
    ) -> None:
        """Execute a graph in the background with log streaming support."""
        
        # Initialize run storage
        runs[run_id] = {
            "status": "running",
            "state": initial_state,
            "history": []
        }
        run_logs[run_id] = []
        
        async def log_callback(event: Dict[str, Any]):
            """Callback to store and broadcast log events."""
            # Store log
            run_logs[run_id].append(event)
            
            # Broadcast to all subscribers
            if run_id in run_subscribers:
                disconnected = set()
                for websocket in run_subscribers[run_id]:
                    try:
                        await websocket.send_json(event)
                    except Exception as e:
                        logger.warning(f"Failed to send to websocket: {e}")
                        disconnected.add(websocket)
                
                # Remove disconnected websockets
                run_subscribers[run_id] -= disconnected
        
        try:
            # Execute graph asynchronously with callback
            result = await graph.run_async(initial_state, callback=log_callback)
            
            # Update run status
            runs[run_id].update({
                "status": "completed",
                "state": result["final_state"],
                "history": result["history"]
            })
            
            logger.info(f"Run {run_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Run {run_id} failed: {e}")
            runs[run_id].update({
                "status": "failed",
                "error": str(e),
                "state": initial_state,
                "history": []
            })
            
            # Send failure event to subscribers
            failure_event = {
                "type": "execution_failed",
                "data": {"error": str(e)}
            }
            await log_callback(failure_event)
        
        finally:
            # Cleanup task reference
            if run_id in self.tasks:
                del self.tasks[run_id]
    
    def start_execution(
        self, 
        graph: Graph, 
        initial_state: Dict[str, Any],
        run_id: Optional[str] = None
    ) -> str:
        """Start a graph execution in the background."""
        if run_id is None:
            run_id = str(uuid.uuid4())
        
        # Create and store the task
        task = asyncio.create_task(
            self.execute_graph(run_id, graph, initial_state)
        )
        self.tasks[run_id] = task
        
        return run_id
    
    def get_task_status(self, run_id: str) -> Optional[str]:
        """Get the status of a running task."""
        if run_id in self.tasks:
            task = self.tasks[run_id]
            if task.done():
                return "completed" if not task.exception() else "failed"
            return "running"
        return None

# Global task manager instance
task_manager = BackgroundTaskManager()
