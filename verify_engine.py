import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_sample_workflow():
    print("\n--- Testing Sample Workflow (Code Review) ---")
    
    # 1. Create Graph
    resp = requests.post(f"{BASE_URL}/graph/create_sample")
    resp.raise_for_status()
    graph_id = resp.json()["graph_id"]
    print(f"Graph Created: {graph_id}")

    # 2. Run Graph
    initial_state = {
        "raw_code": "def hello():\n    print('world')\n    # TODO: fix me\n    a=1\n    b=2\n    c=3\n    d=4\n    e=5\n    f=6\n    g=7\n    h=8" 
        # Long code to trigger complexity?
    }
    resp = requests.post(f"{BASE_URL}/graph/run", json={
        "graph_id": graph_id,
        "initial_state": initial_state
    })
    resp.raise_for_status()
    run_data = resp.json()
    run_id = run_data["run_id"]
    print(f"Run Started: {run_id}")
    
    # 3. Poll State
    for _ in range(10):
        resp = requests.get(f"{BASE_URL}/graph/state/{run_id}")
        data = resp.json()
        status = data["status"]
        print(f"Status: {status}")
        if status == "completed":
            print("Completed!")
            print("Final State Keys:", data["state"].keys())
            print("Complexity Score:", data["state"].get("complexity_score"))
            print("Suggestions:", data["state"].get("suggestions"))
            print("Step Count:", len(data["history"]))
            break
        elif status == "failed":
            print("Failed!")
            break
        time.sleep(1)

def test_dynamic_graph():
    print("\n--- Testing Dynamic Graph Creation ---")
    # Create simple graph: extract -> complexity
    payload = {
        "nodes": {
            "Step1": "extract_code",
            "Step2": "check_complexity"
        },
        "edges": {
            "Step1": "Step2"
        },
        "start": "Step1"
    }
    
    resp = requests.post(f"{BASE_URL}/graph/create", json=payload)
    if resp.status_code != 200:
        print("Error creating dynamic graph:", resp.text)
        return
    
    graph_id = resp.json()["graph_id"]
    print(f"Dynamic Graph Created: {graph_id}")
    
    # Run
    resp = requests.post(f"{BASE_URL}/graph/run", json={
        "graph_id": graph_id,
        "initial_state": {"raw_code": "def foo(): pass"}
    })
    run_id = resp.json()["run_id"]
    print(f"Run Started: {run_id}")
    
    # Poll
    time.sleep(1)
    resp = requests.get(f"{BASE_URL}/graph/state/{run_id}")
    data = resp.json()
    print("Final State Keys:", data["state"].keys())

if __name__ == "__main__":
    try:
        test_sample_workflow()
        test_dynamic_graph()
    except Exception as e:
        print(f"Verification Failed: {e}")
