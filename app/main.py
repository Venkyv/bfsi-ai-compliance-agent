"""
app/main.py

FastAPI application entry point.

Usage:
    python app/main.py
    uvicorn app.main:app --reload --port 8000

API docs: http://localhost:8000/docs
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.routes import app
from app.config import config

if __name__ == "__main__":
    import uvicorn

    issues = config.validate()
    # Remove HuggingFace warning for API-only runs
    issues = [i for i in issues if "HUGGINGFACE" not in i]
    if issues:
        for issue in issues:
            print(f"[CONFIG ERROR] {issue}")
        sys.exit(1)

    print(f"\n  BFSI Compliance Agent — FastAPI")
    print(f"  LLM Provider : {config.LLM_PROVIDER.upper()}")
    print(f"  API docs     : http://localhost:{config.API_PORT}/docs")
    print(f"  Health check : http://localhost:{config.API_PORT}/health\n")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=config.API_PORT,
        reload=True,
    )
