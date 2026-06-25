"""FastAPI composition root (Phase 2 scaffold)."""

from __future__ import annotations

import httpx
from fastapi import FastAPI, Response
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .adapters.db.engine import create_engine
from .config import get_settings

app = FastAPI(title="FitSci Evaluator", version="0.1.0")


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
async def readyz(response: Response) -> dict[str, object]:
    settings = get_settings()
    checks: dict[str, object] = {}

    engine = create_engine(settings)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except SQLAlchemyError as exc:
        checks["postgres"] = f"error: {exc}"
    finally:
        await engine.dispose()

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            tags_response = await client.get(
                f"{settings.ollama_base_url.rstrip('/')}/api/tags"
            )
            tags_response.raise_for_status()
        checks["ollama"] = "ok"
    except httpx.HTTPError as exc:
        checks["ollama"] = f"error: {exc}"

    checks["rabbitmq"] = "skipped"
    postgres_ok = checks.get("postgres") == "ok"
    ollama_ok = checks.get("ollama") == "ok"
    if not (postgres_ok and ollama_ok):
        response.status_code = 503

    return {
        "status": "ready" if postgres_ok and ollama_ok else "not_ready",
        "deployment": settings.deployment,
        "checks": checks,
    }
