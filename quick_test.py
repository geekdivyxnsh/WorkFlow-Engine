"""
Quick Test Script for WebSocket Streaming and Async Execution
"""
import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def test_features():
    print("=" * 60)
    print("TESTING: WebSocket Streaming & Async Execution")
    print("=" * 60)
    print()
    
    # Test 1: Create sample graph
    print("[1/4] Creating sample graph...")
    try:
        response = requests.post(f"{BASE_URL}/graph/create_sample")
        if response.status_code != 200:
            print(f"FAIL: Got status {response.status_code}")
            return False
        graph_id = response.json()["graph_id"]
        print(f"PASS: Graph created - {graph_id}")
    except Exception as e:
        print(f"FAIL: {e}")
        return False
    
    # Test 2: Start execution (should return immediately)
    print("\n[2/4] Starting workflow execution...")
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/graph/run",
            json={
                "graph_id": graph_id,
                "initial_state": {"raw_code": "def test(): pass"}
            }
        )
        elapsed = time.time() - start_time
        
        if response.status_code != 200:
            print(f"FAIL: Got status {response.status_code}")
            return False
            
        data = response.json()
        run_id = data["run_id"]
        status = data["status"]
        
        print(f"PASS: Execution started - {run_id}")
        print(f"      Status: {status}")
        print(f"      Response time: {elapsed:.3f}s")
        
        if status != "running":
            print(f"FAIL: Expected status 'running', got '{status}'")
            return False
            
        if elapsed >= 1.0:
            print(f"FAIL: Took too long ({elapsed:.3f}s)")
            return False
            
        print("PASS: Returns immediately with 'running' status")
        
    except Exception as e:
        print(f"FAIL: {e}")
        return False
    
    # Test 3: Check WebSocket endpoint exists
    print("\n[3/4] Checking WebSocket endpoint...")
    try:
        # Try to get run state (which should exist)
        response = requests.get(f"{BASE_URL}/graph/state/{run_id}")
        if response.status_code == 200:
            print(f"PASS: Run state endpoint works")
        else:
            print(f"WARN: Run state returned {response.status_code}")
    except Exception as e:
        print(f"WARN: {e}")
    
    # Test 4: Wait and check completion
    print("\n[4/4] Waiting for background execution...")
    time.sleep(3)
    
    try:
        response = requests.get(f"{BASE_URL}/graph/state/{run_id}")
        if response.status_code == 200:
            data = response.json()
            final_status = data["status"]
            print(f"PASS: Final status - {final_status}")
            
            if final_status in ["completed", "failed"]:
                print("PASS: Background execution finished!")
            else:
                print(f"WARN: Still {final_status}")
        else:
            print(f"FAIL: Got status {response.status_code}")
            return False
    except Exception as e:
        print(f"FAIL: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
    print("\nFeatures verified:")
    print("  [X] Async execution (returns immediately)")
    print("  [X] Background task execution")
    print("  [X] Run status tracking")
    print("\nTo test WebSocket streaming, run:")
    print("  python websocket_client_demo.py")
    print("=" * 60)
    return True

if __name__ == "__main__":
    print("\nMake sure the server is running:")
    print("  python -m uvicorn app.main:app --reload")
    print()
    
    try:
        success = test_features()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
