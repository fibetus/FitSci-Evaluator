"""True end-to-end test for the async evaluation workflow (DoD of Phase 2).

Exercises the real path: HTTP POST -> RabbitMQ -> Worker -> Postgres -> HTTP GET.
Both the message broker and the database are real (testcontainers). Only the LLM
(Ollama/Gemma) is faked, because the broker DoD is about the async plumbing, not
extraction quality (which is covered by the benchmark + adapter unit tests).
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from datetime import timedelta

import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("FITSCI_INTEGRATION") != "1",
        reason="Set FITSCI_INTEGRATION=1 to run end-to-end integration tests",
    ),
]

pytest.importorskip("testcontainers.rabbitmq")
pytest.importorskip("testcontainers.postgres")


@dataclass
class _E2EContainer:
    submit_evaluation: object
    get_job: object


class _OkIngestor:
    async def fetch_by_id(self, study_id: str) -> str:
        return "paper text"

    async def search(self, query: str, limit: int = 10) -> list[str]:
        return []


class _OkEvaluator:
    async def evaluate_text(self, text: str):
        from src.domain.models.extraction import ExtractionResult

        return ExtractionResult(
            id="PMC-IGNORED",
            pmc_url="https://example.com",
            title="T",
            authors=["A"],
            journal="J",
            year=2024,
            impact_factor=1.0,
            type="rct",
            topic="protein",
            subtopic="x",
            sample_size=10,
            primary_outcome="Y",
        )


@pytest.mark.anyio
async def test_evaluate_end_to_end_http_rabbitmq_worker_postgres() -> None:
    import aio_pika  # noqa: F401  (ensures broker deps present)
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient
    from testcontainers.postgres import PostgresContainer
    from testcontainers.rabbitmq import RabbitMqContainer

    from src.adapters.api.v1.router import router
    from src.adapters.broker.rabbitmq_adapter import RabbitMQAdapter
    from src.adapters.db.engine import (
        create_engine,
        create_session_factory,
        init_schema,
    )
    from src.adapters.db.postgres_job_repository import PostgresJobRepository
    from src.adapters.db.postgres_study_repository import PostgresStudyRepository
    from src.adapters.system.clock import SystemClock
    from src.application.use_cases.evaluate_study import EvaluateStudyUseCase
    from src.application.use_cases.get_job import GetJobUseCase
    from src.application.use_cases.process_evaluation_job import (
        ProcessEvaluationJobUseCase,
    )
    from src.application.use_cases.submit_evaluation import SubmitEvaluationUseCase
    from src.config.settings import Settings
    from src.domain.ports.logger import NullLogger

    with PostgresContainer("postgres:16-alpine") as postgres, RabbitMqContainer(
        "rabbitmq:3.13-management-alpine"
    ) as rabbit:
        sync_url = postgres.get_connection_url()
        async_url = sync_url.replace(
            "postgresql+psycopg2://", "postgresql+asyncpg://", 1
        ).replace("postgresql://", "postgresql+asyncpg://", 1)
        settings = Settings(
            deployment="local",
            postgres_dsn=async_url,
            postgres_sync_dsn=sync_url.replace(
                "postgresql://", "postgresql+psycopg://", 1
            ),
            rabbitmq_url=rabbit.get_connection_url(),
            ollama_base_url="http://localhost:11434",
            gemma_model_tag="gemma4:12b-q4_k_m",
            log_level="INFO",
            rate_limit_per_minute=30,
            ncbi_api_key=None,
            rabbitmq_evaluation_queue="fitsci.e2e.jobs",
            evaluation_idempotency_hours=24,
        )

        engine = create_engine(settings)
        await init_schema(engine)
        factory = create_session_factory(engine)

        clock = SystemClock()
        logger = NullLogger()
        studies = PostgresStudyRepository(factory)
        jobs = PostgresJobRepository(factory)
        queue = RabbitMQAdapter(
            settings.rabbitmq_url,
            queue_name=settings.rabbitmq_evaluation_queue,
            requeue_delay_seconds=0.0,
        )
        evaluate = EvaluateStudyUseCase(
            ingestor=_OkIngestor(),
            evaluator=_OkEvaluator(),
            repository=studies,
            logger=logger,
            clock=clock,
        )
        container = _E2EContainer(
            submit_evaluation=SubmitEvaluationUseCase(
                jobs=jobs,
                queue=queue,
                clock=clock,
                logger=logger,
                idempotency_window=timedelta(hours=24),
            ),
            get_job=GetJobUseCase(jobs=jobs, studies=studies),
        )
        process = ProcessEvaluationJobUseCase(
            evaluate=evaluate, jobs=jobs, clock=clock, logger=logger
        )

        app = FastAPI()
        app.state.container = container
        app.include_router(router)

        await queue.connect()
        consume_task = asyncio.create_task(
            queue.consume_evaluation_jobs(process.execute)
        )

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                post = await client.post(
                    "/api/v1/evaluate", json={"pmc_id": "PMC777"}
                )
                assert post.status_code == 202
                job_id = post.json()["job_id"]

                final = None
                for _ in range(100):
                    res = await client.get(f"/api/v1/jobs/{job_id}")
                    body = res.json()
                    if body["status"] in {"succeeded", "failed"}:
                        final = body
                        break
                    await asyncio.sleep(0.1)

                assert final is not None, "job did not reach a terminal state"
                assert final["status"] == "succeeded"
                assert final["study"] is not None
                assert final["study"]["id"] == "PMC777"

            # Confirm the study really landed in Postgres (not just in the response).
            stored = await studies.get_by_id("PMC777")
            assert stored is not None
        finally:
            consume_task.cancel()
            try:
                await consume_task
            except asyncio.CancelledError:
                pass
            await queue.close()
            await engine.dispose()
