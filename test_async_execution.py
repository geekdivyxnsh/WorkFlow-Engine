"""
Test: Async Execution Returns Immediately
Verifies that /graph/run returns immediately with status 'running'
"""
import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_async_execution():
    print("=" * 60)
    print("TEST: Async Execution Returns Immediately")
    print("=" * 60)
    print()
    
    # Create sample graph
    print("Creating sample graph...")
    response = requests.post(f"{BASE_URL}/graph/create_sample")
    assert response.status_code == 200
    graph_id = response.json()["graph_id"]
    print(f"Graph created: {graph_id}")
    
    # Start execution and measure time
    print("\nStarting workflow execution...")
    start_time = time.time()
    
    response = requests.post(
        f"{BASE_URL}/graph/run",
        json={
            "graph_id": graph_id,
            "initial_state": {"raw_code": "def test(): pass"}
        }
    )
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    assert response.status_code == 200
    data = response.json()
    run_id = data["run_id"]
    status = data["status"]
    
    print(f"Response received in {elapsed:.3f} seconds")
    print(f"  Run ID: {run_id}")
    print(f"  Status: {status}")
    
    # Verify it returns immediately (< 1 second)
    if elapsed < 1.0:
        print(f"\nPASS: Returned immediately ({elapsed:.3f}s < 1.0s)")
    else:
        print(f"\nFAIL: Took too long ({elapsed:.3f}s >= 1.0s)")
        return False
    
    # Verify status is "running"
    if status == "running":
        print("PASS: Status is 'running'")
    else:
        print(f"FAIL: Status is '{status}', expected 'running'")
        return False
    
    # Wait a bit and check if it completed
    print("\nWaiting 2 seconds for execution to complete...")
    time.sleep(2)
    
    response = requests.get(f"{BASE_URL}/graph/state/{run_id}")
    assert response.status_code == 200
    final_data = response.json()
    final_status = final_data["status"]
    
    print(f"  Final Status: {final_status}")
    
    if final_status in ["completed", "failed"]:
        print("PASS: Execution finished in background")
    else:
        print(f"WARNING: Still {final_status}")
    
    print("\n" + "=" * 60)
    print("TEST PASSED!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = test_async_execution()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\nTEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
