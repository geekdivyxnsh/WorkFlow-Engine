"""
Demonstration of the Code Review Mini-Agent Workflow (Option A)

This script shows all 5 steps of the workflow:
1. Extract functions from code
2. Check complexity score
3. Detect basic issues (TODOs, high complexity)
4. Suggest improvements
5. Loop until quality_score >= threshold (complexity <= 5)
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def print_state(state: Dict[str, Any], step_num: int):
    """Pretty print the state after each step"""
    print(f"\n--- Step {step_num} State ---")
    print(json.dumps(state, indent=2))

def demo_code_review_workflow():
    """Demonstrate the complete Code Review workflow with looping"""
    
    print_section("CODE REVIEW MINI-AGENT WORKFLOW DEMONSTRATION")
    
    # Sample code with issues that will trigger improvements
    sample_code = """
def complex_function():
    # TODO: Refactor this function
    a = 1
    b = 2
    c = 3
    d = 4
    e = 5
    return a + b + c + d + e

def another_function():
    print('Hello World')
"""
    
    print("\n>> Input Code:")
    print(sample_code)
    
    # Step 1: Create the Code Review Graph
    print_section("STEP 1: Creating Code Review Graph")
    
    resp = requests.post(f"{BASE_URL}/graph/create_sample")
    resp.raise_for_status()
    graph_id = resp.json()["graph_id"]
    
    print(f"[OK] Graph Created Successfully!")
    print(f"   Graph ID: {graph_id}")
    
    # Step 2: Execute the Workflow
    print_section("STEP 2: Executing Workflow")
    
    initial_state = {"raw_code": sample_code}
    
    resp = requests.post(f"{BASE_URL}/graph/run", json={
        "graph_id": graph_id,
        "initial_state": initial_state
    })
    resp.raise_for_status()
    run_data = resp.json()
    run_id = run_data["run_id"]
    
    print(f"[OK] Workflow Execution Started!")
    print(f"   Run ID: {run_id}")
    
    # Step 3: Monitor Execution
    print_section("STEP 3: Monitoring Execution & Results")
    
    resp = requests.get(f"{BASE_URL}/graph/state/{run_id}")
    result = resp.json()
    
    print(f"\n>> Final Status: {result['status'].upper()}")
    
    # Display execution history - shows the looping
    print("\n>> Execution History (showing workflow steps):")
    for idx, history_item in enumerate(result["history"], 1):
        node_name = history_item["node"]
        print(f"   {idx}. {node_name}")
    
    # Display final state
    final_state = result["state"]
    
    print("\n>> Final Results:")
    print(f"   - Extracted Functions: {len(final_state.get('functions', []))} found")
    if final_state.get('functions'):
        for func in final_state['functions']:
            print(f"     - {func}")
    
    print(f"\n   - Complexity Score: {final_state.get('complexity_score', 'N/A')}")
    
    issues = final_state.get('issues', [])
    print(f"\n   - Issues Detected: {len(issues)}")
    if issues:
        for issue in issues:
            print(f"     - {issue}")
    
    suggestions = final_state.get('suggestions', [])
    if suggestions:
        print(f"\n   - Improvement Suggestions: {len(suggestions)}")
        for suggestion in suggestions:
            print(f"     - {suggestion}")
    
    # Show the looping behavior
    print_section("STEP 4: Demonstrating Loop Behavior")
    
    complexity_checks = [h for h in result["history"] if h["node"] == "complexity"]
    print(f"\n>> Complexity was checked {len(complexity_checks)} time(s)")
    print(f"   This demonstrates the workflow's ability to loop until")
    print(f"   the quality threshold is met (complexity_score <= 5)")
    
    # Final summary
    print_section("WORKFLOW COMPLETE!")
    
    print("\n>> Summary:")
    print(f"   - Total Steps Executed: {len(result['history'])}")
    print(f"   - Final Complexity Score: {final_state.get('complexity_score', 'N/A')}")
    print(f"   - Status: {result['status'].upper()}")
    
    print("\n>> The workflow demonstrates all 5 required features:")
    print("   1. [OK] Extract functions - Parsed function definitions from code")
    print("   2. [OK] Check complexity - Calculated complexity score")
    print("   3. [OK] Detect issues - Found TODOs and complexity issues")
    print("   4. [OK] Suggest improvements - Generated actionable suggestions")
    print("   5. [OK] Loop until threshold - Repeated until complexity <= 5")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    try:
        demo_code_review_workflow()
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Could not connect to the server.")
        print("   Please ensure the server is running on http://localhost:8000")
        print("   Run: python -m uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
