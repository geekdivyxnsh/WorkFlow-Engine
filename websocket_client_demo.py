"""
WebSocket Client Demo for Workflow Engine
Demonstrates real-time log streaming from workflow execution
"""
import asyncio
import websockets
import json
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

async def demo_websocket_streaming():
    """Demonstrates WebSocket streaming of workflow execution logs."""
    
    print("=" * 60)
    print("WORKFLOW ENGINE - WebSocket Streaming Demo")
    print("=" * 60)
    print()
    
    # Step 1: Create sample graph
    print("Step 1: Creating Code Review Mini-Agent graph...")
    response = requests.post(f"{BASE_URL}/graph/create_sample")
    graph_id = response.json()["graph_id"]
    print(f"Graph created: {graph_id}")
    print()
    
    # Step 2: Start execution
    print("Step 2: Starting workflow execution...")
    initial_state = {
        "raw_code": """
def complex_function():
    # TODO: refactor this
    x = 1
    y = 2
    return x + y
"""
    }
    
    response = requests.post(
        f"{BASE_URL}/graph/run",
        json={
            "graph_id": graph_id,
            "initial_state": initial_state
        }
    )
    run_data = response.json()
    run_id = run_data["run_id"]
    print(f"Execution started: {run_id}")
    print(f"  Status: {run_data['status']}")
    print()
    
    # Step 3: Connect to WebSocket and stream logs
    print("Step 3: Connecting to WebSocket for real-time logs...")
    print("-" * 60)
    
    ws_url = f"{WS_URL}/ws/run/{run_id}"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"Connected to {ws_url}")
            print()
            print("STREAMING EXECUTION LOGS:")
            print("=" * 60)
            
            step_count = 0
            
            while True:
                try:
                    # Receive log event
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    event = json.loads(message)
                    
                    event_type = event.get("type", "unknown")
                    timestamp = event.get("timestamp", "")
                    data = event.get("data", {})
                    
                    # Format and display based on event type
                    if event_type == "execution_started":
                        print(f"\nEXECUTION STARTED")
                        print(f"   Entry Point: {data.get('entry_point')}")
                        
                    elif event_type == "step_start":
                        step_count += 1
                        print(f"\nSTEP {data.get('step')}: {data.get('node')}")
                        print(f"   Node: {data.get('node')}")
                        
                    elif event_type == "step_complete":
                        print(f"   Completed")
                        updates = data.get('updates', {})
                        if updates:
                            print(f"   Updates: {json.dumps(updates, indent=6)}")
                    
                    elif event_type == "transition":
                        from_node = data.get('from_node')
                        to_node = data.get('to_node')
                        if to_node:
                            condition_met = data.get('condition_met')
                            if condition_met is None:
                                print(f"   Next: {to_node} (unconditional)")
                            else:
                                print(f"   Next: {to_node} (condition: {condition_met})")
                        else:
                            print(f"   No next node (workflow ending)")
                    
                    elif event_type == "execution_complete":
                        print(f"\nEXECUTION COMPLETE")
                        print(f"   Total Steps: {data.get('total_steps')}")
                        print(f"   Final State:")
                        final_state = data.get('final_state', {})
                        for key, value in final_state.items():
                            if not key.startswith('_'):
                                print(f"     - {key}: {value}")
                        break
                    
                    elif event_type == "execution_failed":
                        print(f"\nEXECUTION FAILED")
                        print(f"   Error: {data.get('error')}")
                        break
                    
                    elif event_type == "status_update":
                        print(f"\nStatus: {data.get('status')}")
                    
                    elif event_type == "error":
                        print(f"\nError: {data.get('error')}")
                        break
                    
                except asyncio.TimeoutError:
                    print("\nNo more events (timeout)")
                    break
                except websockets.exceptions.ConnectionClosed:
                    print("\nConnection closed")
                    break
                    
    except Exception as e:
        print(f"\nWebSocket error: {e}")
    
    print()
    print("=" * 60)
    print("Demo Complete!")
    print("=" * 60)

if __name__ == "__main__":
    print("\nMake sure the server is running:")
    print("  python -m uvicorn app.main:app --reload")
    print("\nPress Ctrl+C to exit\n")
    
    try:
        asyncio.run(demo_websocket_streaming())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
