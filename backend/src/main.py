"""FastAPI composition root (Phase 2)."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx
from fastapi import FastAPI, Response
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .adapters.api.v1.router import router as v1_router
from .adapters.broker.rabbitmq_adapter import RabbitMQAdapter
from .adapters.db.engine import create_engine
from .composition import AppContainer
from .config import get_settings

_settings = get_settings()
_container = AppContainer(_settings)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await _container.startup()
    app.state.container = _container
    yield
    await _container.shutdown()


app = FastAPI(title="FitSci Evaluator", version="0.1.0", lifespan=lifespan)
app.include_router(v1_router)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
async def readyz(response: Response) -> dict[str, object]:
    settings = get_settings()
    checks: dict[str, object] = {}

    engine = None
    try:
        engine = create_engine(settings)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception:
        checks["postgres"] = "error"
    finally:
        if engine is not None:
            await engine.dispose()

    try:
        probe = RabbitMQAdapter(
            settings.rabbitmq_url,
            queue_name=settings.rabbitmq_evaluation_queue,
        )
        await probe.connect()
        await probe.close()
        checks["rabbitmq"] = "ok"
    except Exception:
        checks["rabbitmq"] = "error"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            tags_response = await client.get(
                f"{settings.ollama_base_url.rstrip('/')}/api/tags"
            )
            tags_response.raise_for_status()
        checks["ollama"] = "ok"
    except httpx.HTTPError:
        checks["ollama"] = "error"

    postgres_ok = checks.get("postgres") == "ok"
    rabbitmq_ok = checks.get("rabbitmq") == "ok"
    ollama_ok = checks.get("ollama") == "ok"
    if not (postgres_ok and rabbitmq_ok and ollama_ok):
        response.status_code = 503

    return {
        "status": "ready" if postgres_ok and rabbitmq_ok and ollama_ok else "not_ready",
        "deployment": settings.deployment,
        "checks": checks,
    }
