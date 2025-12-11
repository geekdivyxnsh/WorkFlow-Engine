# Workflow Engine

## How to run
- Install: `pip install -r requirements.txt`
- Start server: `python -m uvicorn app.main:app --reload`
- API docs: `http://localhost:8000/docs`

## What the workflow engine supports
- Define nodes, edges, and shared state
- Conditional branching with simple rules
- Looping with safety caps
- Tool registry with built-in tools and safe fallbacks
- Endpoints: `POST /graph/create`, `POST /graph/run?sync=true`, `GET /graph/state/{run_id}`
- Optional: WebSocket logs at `ws://localhost:8000/ws/run/{run_id}`

## What I would improve with more time
- Persistence with SQLite/Postgres for graphs and runs
- Parallel execution and retry logic
- Better observability: metrics, structured logs, tracing
- Plugin tool system with validation and versioning