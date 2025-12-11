from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from app.storage import runs, run_logs, run_subscribers
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/run/{run_id}")
async def websocket_run_stream(websocket: WebSocket, run_id: str):
    """
    WebSocket endpoint for streaming execution logs in real-time.
    
    Connects to a running workflow execution and streams log events as they occur.
    Send JSON messages with format:
    {
        "type": "execution_started|step_start|step_complete|transition|execution_complete|execution_failed",
        "timestamp": "ISO timestamp",
        "data": {...}
    }
    """
    await websocket.accept()
    
    # Check if run exists
    if run_id not in runs:
        await websocket.send_json({
            "type": "error",
            "data": {"error": "Run not found"}
        })
        await websocket.close()
        return
    
    # Register subscriber
    if run_id not in run_subscribers:
        run_subscribers[run_id] = set()
    run_subscribers[run_id].add(websocket)
    
    try:
        # Send all historical logs first
        if run_id in run_logs:
            for log_event in run_logs[run_id]:
                await websocket.send_json(log_event)
        
        # Send current status
        run_data = runs[run_id]
        await websocket.send_json({
            "type": "status_update",
            "timestamp": "",
            "data": {
                "status": run_data["status"],
                "run_id": run_id
            }
        })
        
        # Keep connection alive and wait for client disconnect
        # New events will be pushed via the callback in task_manager
        while True:
            # Just receive messages to keep connection alive
            # Client can send ping/pong or close connection
            try:
                data = await websocket.receive_text()
                # Echo back for ping/pong
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
            except WebSocketDisconnect:
                break
                
    except Exception as e:
        logger.error(f"WebSocket error for run {run_id}: {e}")
    finally:
        # Unregister subscriber
        if run_id in run_subscribers:
            run_subscribers[run_id].discard(websocket)
            if not run_subscribers[run_id]:
                del run_subscribers[run_id]
        
        try:
            await websocket.close()
        except:
            pass
