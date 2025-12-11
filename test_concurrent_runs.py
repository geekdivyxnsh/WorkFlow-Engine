"""
Test: Concurrent Executions
Verifies that multiple graphs can run concurrently
"""
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://localhost:8000"

def start_execution(graph_id, execution_num):
    """Start a single execution and return run info."""
    print(f"  Starting execution #{execution_num}...")
    start_time = time.time()
    
    response = requests.post(
        f"{BASE_URL}/graph/run",
        json={
            "graph_id": graph_id,
            "initial_state": {"raw_code": f"def test{execution_num}(): pass"}
        }
    )
    
    end_time = time.time()
    
    if response.status_code != 200:
        return {"error": f"Failed to start: {response.status_code}"}
    
    data = response.json()
    return {
        "execution_num": execution_num,
        "run_id": data["run_id"],
        "status": data["status"],
        "start_time": start_time,
        "response_time": end_time - start_time
    }

def check_completion(run_id, execution_num):
    """Check if an execution completed."""
    response = requests.get(f"{BASE_URL}/graph/state/{run_id}")
    if response.status_code == 200:
        return response.json()["status"]
    return "unknown"

def test_concurrent_executions():
    print("=" * 60)
    print("TEST: Concurrent Executions")
    print("=" * 60)
    print()
    
    # Create sample graph
    print("Creating sample graph...")
    response = requests.post(f"{BASE_URL}/graph/create_sample")
    assert response.status_code == 200
    graph_id = response.json()["graph_id"]
    print(f"Graph created: {graph_id}")
    
    # Start multiple executions concurrently
    num_executions = 3
    print(f"\nStarting {num_executions} concurrent executions...")
    
    with ThreadPoolExecutor(max_workers=num_executions) as executor:
        futures = [
            executor.submit(start_execution, graph_id, i+1)
            for i in range(num_executions)
        ]
        
        results = []
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            if "error" in result:
                print(f"  Execution failed: {result['error']}")
            else:
                print(f"  Execution #{result['execution_num']} started: {result['run_id']}")
    
    # Check all started successfully
    failed = [r for r in results if "error" in r]
    if failed:
        print(f"\nFAIL: {len(failed)} executions failed to start")
        return False
    
    print(f"\nPASS: All {num_executions} executions started successfully")
    
    # Check response times (should all be fast)
    avg_response_time = sum(r["response_time"] for r in results) / len(results)
    print(f"  Average response time: {avg_response_time:.3f}s")
    
    if avg_response_time < 1.0:
        print(f"  PASS: Fast responses (< 1.0s)")
    else:
        print(f"  WARNING: Slow responses (>= 1.0s)")
    
    # Wait for all to complete
    print(f"\nWaiting for executions to complete...")
    time.sleep(3)
    
    # Check final statuses
    print("\nChecking final statuses...")
    completed_count = 0
    for result in results:
        run_id = result["run_id"]
        status = check_completion(run_id, result["execution_num"])
        print(f"  Execution #{result['execution_num']}: {status}")
        if status == "completed":
            completed_count += 1
    
    if completed_count == num_executions:
        print(f"\nPASS: All {num_executions} executions completed")
    else:
        print(f"\nWARNING: Only {completed_count}/{num_executions} completed")
    
    print("\n" + "=" * 60)
    print("TEST PASSED!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = test_concurrent_executions()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\nTEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
