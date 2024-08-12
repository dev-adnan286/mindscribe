# MindScribe backend

FastAPI service for MindScribe. See the repository root `README.md` for the full
architecture, setup, environment variables and API reference.

Quick start:

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
pytest
```
