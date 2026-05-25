# Backend — AI Engineering Team

FastAPI + LangGraph service that orchestrates the multi-agent workflow.

```bash
python -m venv .venv && . .venv/Scripts/activate   # or source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000          # http://localhost:8000/docs
pytest                                             # run the test suite
python scripts/run_workflow.py "your idea here"    # run the graph in the terminal
```

See the root [README](../README.md), [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)
and [docs/WORKFLOW.md](../docs/WORKFLOW.md) for the full picture.
