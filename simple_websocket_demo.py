"""
Simple WebSocket Demo - ASCII only for Windows compatibility
"""
import asyncio
import websockets
import json
import requests

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

async def simple_websocket_demo():
    print("=" * 70)
    print("WORKFLOW ENGINE - WebSocket Streaming Demo")
    print("=" * 70)
    print()
    
    # Create sample graph
    print("Creating Code Review Mini-Agent graph...")
    response = requests.post(f"{BASE_URL}/graph/create_sample")
    graph_id = response.json()["graph_id"]
    print(f"[OK] Graph created: {graph_id}")
    print()
    
    # Start execution
    print("Starting workflow execution...")
    initial_state = {
        "raw_code": "def complex_function():\n    # TODO: refactor\n    pass"
    }
    
    response = requests.post(
        f"{BASE_URL}/graph/run",
        json={"graph_id": graph_id, "initial_state": initial_state}
    )
    run_data = response.json()
    run_id = run_data["run_id"]
    print(f"[OK] Execution started: {run_id}")
    print(f"[OK] Status: {run_data['status']}")
    print()
    
    # Connect to WebSocket
    print("Connecting to WebSocket for real-time logs...")
    print("-" * 70)
    
    ws_url = f"{WS_URL}/ws/run/{run_id}"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"[OK] Connected to {ws_url}")
            print()
            print("STREAMING EXECUTION LOGS:")
            print("=" * 70)
            
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    event = json.loads(message)
                    
                    event_type = event.get("type", "unknown")
                    data = event.get("data", {})
                    
                    # Display events
                    if event_type == "execution_started":
                        print(f"\n[START] Execution began at node: {data.get('entry_point')}")
                        
                    elif event_type == "step_start":
                        step = data.get('step')
                        node = data.get('node')
                        print(f"\n[STEP {step}] Executing node: {node}")
                        
                    elif event_type == "step_complete":
                        print(f"  -> Completed")
                        updates = data.get('updates', {})
                        if updates:
                            for key, value in updates.items():
                                if key != 'state_snapshot':
                                    print(f"     {key}: {value}")
                    
                    elif event_type == "transition":
                        to_node = data.get('to_node')
                        if to_node:
                            print(f"  -> Transitioning to: {to_node}")
                        else:
                            print(f"  -> No next node (ending)")
                    
                    elif event_type == "execution_complete":
                        print(f"\n[COMPLETE] Execution finished!")
                        print(f"Total steps: {data.get('total_steps')}")
                        final_state = data.get('final_state', {})
                        print("\nFinal State:")
                        for key, value in final_state.items():
                            if not key.startswith('_'):
                                print(f"  - {key}: {value}")
                        break
                    
                    elif event_type == "execution_failed":
                        print(f"\n[FAILED] Error: {data.get('error')}")
                        break
                    
                    elif event_type == "status_update":
                        print(f"[STATUS] {data.get('status')}")
                    
                except asyncio.TimeoutError:
                    print("\n[TIMEOUT] No more events")
                    break
                except websockets.exceptions.ConnectionClosed:
                    print("\n[CLOSED] Connection closed")
                    break
                    
    except Exception as e:
        print(f"\n[ERROR] WebSocket error: {e}")
        return False
    
    print()
    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    print("\nServer should be running on http://localhost:8000")
    print()
    
    try:
        asyncio.run(simple_websocket_demo())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted.")
