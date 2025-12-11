@echo off
echo Starting Workflow Engine Server...
echo.
python -m uvicorn app.main:app --reload --host localhost --port 8000
