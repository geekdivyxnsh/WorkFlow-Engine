"""Alias module for Render start command.

This exposes `app` from our actual FastAPI entrypoint at `app.main` so
Render's start command `uvicorn fastapi_workflow_engine:app` works.
"""

from app.main import app