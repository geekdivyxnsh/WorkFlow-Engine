from typing import Callable, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

State = Dict[str, Any]

class SmartToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self._register_defaults()

    def register(self, name: Optional[str] = None):
        """Decorator to register a function as a tool."""
        def decorator(func):
            tool_name = name or func.__name__
            self.tools[tool_name] = func
            return func
        return decorator

    def _register_defaults(self):
        """Registers universal built-in tools."""
        
        @self.register("echo")
        def echo(state: State) -> State:
            return {"output": dict(state)}

        @self.register("print")
        def print_tool(state: State) -> State:
            print(f"[PRINT TOOL]: {state}")
            return {}

        @self.register("noop")
        def noop(state: State) -> State:
            return {}
        
        @self.register("passthrough")
        def passthrough(state: State) -> State:
            return {}

        @self.register("sum")
        def sum_tool(state: State) -> State:
            # Tries to sum values if they are numbers list
            values = state.get("values", [])
            if isinstance(values, list) and all(isinstance(x, (int, float)) for x in values):
                return {"sum": sum(values)}
            return {"sum": 0, "error": "Invalid input for sum"}

        @self.register("llm")
        def llm_stub(state: State) -> State:
            # Mock LLM
            prompt = state.get("prompt", "")
            return {"llm_response": f"Mock response for: {prompt[:20]}..."}

    def _create_default_tool(self, tool_name: str) -> Callable:
        """Creates a safe fallback tool that never fails."""
        def default_tool(state: State) -> State:
            logger.warning(f"Executing fallback for unknown tool: {tool_name}")
            return {
                "tool_execution": tool_name,
                "status": "fallback_executed", 
                "original_input_keys": list(state.keys())
            }
        
        return default_tool

    def get(self, name: str) -> Callable:
        """
        Retrieves a tool. If not found, dynamically registers and returns 
        a DefaultTool to ensure zero failures.
        """
        if name not in self.tools:
            logger.info(f"Tool '{name}' not found. Auto-registering default fallback.")
            self.tools[name] = self._create_default_tool(name)
        
        return self.tools[name]

# Global registry instance
default_registry = SmartToolRegistry()
