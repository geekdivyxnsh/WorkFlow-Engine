"""
Test: WebSocket Streaming
Verifies that WebSocket endpoint receives step-by-step logs
"""
import asyncio
import websockets
import json
import requests

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

async def test_websocket_streaming():
    print("=" * 60)
    print("TEST: WebSocket Streaming")
    print("=" * 60)
    print()
    
    # Create sample graph
    print("Creating sample graph...")
    response = requests.post(f"{BASE_URL}/graph/create_sample")
    assert response.status_code == 200
    graph_id = response.json()["graph_id"]
    print(f"Graph created: {graph_id}")
    
    # Start execution
    print("\nStarting workflow execution...")
    response = requests.post(
        f"{BASE_URL}/graph/run",
        json={
            "graph_id": graph_id,
            "initial_state": {"raw_code": "def test(): pass"}
        }
    )
    assert response.status_code == 200
    run_id = response.json()["run_id"]
    print(f"Execution started: {run_id}")
    
    # Connect to WebSocket
    print("\nConnecting to WebSocket...")
    ws_url = f"{WS_URL}/ws/run/{run_id}"
    
    events_received = []
    event_types = set()
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"Connected to {ws_url}")
            print("\nReceiving events...")
            
            # Receive events for up to 5 seconds
            timeout = 5.0
            start_time = asyncio.get_event_loop().time()
            
            while True:
                try:
                    remaining = timeout - (asyncio.get_event_loop().time() - start_time)
                    if remaining <= 0:
                        break
                    
                    message = await asyncio.wait_for(
                        websocket.recv(), 
                        timeout=remaining
                    )
                    event = json.loads(message)
                    events_received.append(event)
                    event_type = event.get("type")
                    event_types.add(event_type)
                    print(f"  - Received: {event_type}")
                    
                    # Stop if execution complete
                    if event_type in ["execution_complete", "execution_failed"]:
                        break
                        
                except asyncio.TimeoutError:
                    break
                except websockets.exceptions.ConnectionClosed:
                    break
    
    except Exception as e:
        print(f"\nWebSocket error: {e}")
        return False
    
    # Verify results
    print(f"\nResults:")
    print(f"  Total events received: {len(events_received)}")
    print(f"  Event types: {sorted(event_types)}")
    
    # Check for required event types
    required_events = ["execution_started", "step_start", "step_complete"]
    missing_events = [e for e in required_events if e not in event_types]
    
    if missing_events:
        print(f"\nFAIL: Missing required events: {missing_events}")
        return False
    else:
        print(f"\nPASS: All required events received")
    
    # Check that we got multiple steps
    step_events = [e for e in events_received if e.get("type") == "step_start"]
    if len(step_events) > 0:
        print(f"PASS: Received {len(step_events)} step events (streaming works!)")
    else:
        print(f"FAIL: No step events received")
        return False
    
    print("\n" + "=" * 60)
    print("TEST PASSED!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_websocket_streaming())
        exit(0 if success else 1)
    except Exception as e:
        print(f"\nTEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
