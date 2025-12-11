from app.registry import default_registry
from app.engine import Graph, State
import random

# --- Tools ---

@default_registry.register("extract_code")
def extract_code(state: State) -> State:
    # Simulate extracting code functions
    raw_code = state.get("raw_code", "")
    functions = [line.strip() for line in raw_code.splitlines() if line.strip().startswith("def ")]
    return {"functions": functions}

@default_registry.register("check_complexity")
def check_complexity(state: State) -> State:
    # Deterministic, rule-based complexity measure for demo purposes.
    # If an existing complexity score is present (e.g., after improvements), reuse it.
    if "complexity_score" in state:
        return {"complexity_score": state["complexity_score"]}

    raw_code = state.get("raw_code", "")
    lines = [ln for ln in raw_code.splitlines() if ln.strip()]
    # Simple heuristic: base complexity is number of non-empty lines, capped 1..10
    base = len(lines)
    complexity_score = max(1, min(10, base))
    return {"complexity_score": complexity_score}

@default_registry.register("detect_issues")
def detect_issues(state: State) -> State:
    # Simulate issue detection
    complexity = state.get("complexity_score", 0)
    issues = []
    if complexity > 7:
        issues.append("High complexity detected")
    if "todo" in state.get("raw_code", "").lower():
        issues.append("Found TODO comments")
    
    return {"issues": issues}

@default_registry.register("suggest_improvements")
def suggest_improvements(state: State) -> State:
    # Simulate improvement suggestions
    issues = state.get("issues", [])
    suggestions = []
    if "High complexity detected" in issues:
        suggestions.append("Refactor long functions into smaller ones")
    if "Found TODO comments" in issues:
        suggestions.append("Resolve pending TODOs")
    
    # Simulate improvement by lowering complexity for the loop demonstration
    current_complexity = state.get("complexity_score", 10)
    new_complexity = max(0, current_complexity - 2)
    
    return {"suggestions": suggestions, "complexity_score": new_complexity}

# --- Graph Construction ---

def create_code_review_graph() -> Graph:
    graph = Graph()
    
    # Add nodes
    # We use the registered functions
    graph.add_node("extract", default_registry.get("extract_code"))
    graph.add_node("complexity", default_registry.get("check_complexity"))
    graph.add_node("issues", default_registry.get("detect_issues"))
    graph.add_node("improve", default_registry.get("suggest_improvements"))
    
    # Add edges
    # Linear flow: extract -> complexity -> issues
    graph.add_edge("extract", "complexity")
    graph.add_edge("complexity", "issues")
    
    # Conditional/Looping flow:
    # issues -> improve (if complexity > 5)
    # issues -> END (if complexity <= 5)
    # improve -> complexity (loop back to check if score improved)
    
    # We need a condition function
    def needs_improvement(state: State) -> bool:
        return state.get("complexity_score", 0) > 5

    # If needs improvement, go to 'improve' node
    graph.add_edge("issues", "improve", condition=needs_improvement)
    
    # Loop back
    graph.add_edge("improve", "complexity")
    
    graph.set_entry_point("extract")
    
    return graph
