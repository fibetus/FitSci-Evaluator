from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.adapters.api.v1.router import router
from src.adapters.broker.in_memory_queue import InMemoryMessageQueue
from src.adapters.db.in_memory_job_repository import InMemoryJobRepository
from src.adapters.db.in_memory_repository import InMemoryStudyRepository
from src.adapters.system.clock import SystemClock
from src.application.use_cases.evaluate_study import EvaluateStudyUseCase
from src.application.use_cases.get_job import GetJobUseCase
from src.application.use_cases.process_evaluation_job import ProcessEvaluationJobUseCase
from src.application.use_cases.submit_evaluation import SubmitEvaluationUseCase
from src.domain.models.extraction import ExtractionResult
from src.domain.ports.logger import NullLogger
from src.domain.services.scoring import ScoringService


class _OkIngestor:
    async def fetch_by_id(self, study_id: str) -> str:
        return "paper"

    async def search(self, query: str, limit: int = 10) -> list[str]:
        return []


class _OkEvaluator:
    async def evaluate_text(self, text: str) -> ExtractionResult:
        return ExtractionResult(
            id="PMC1",
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


@dataclass
class ApiTestContainer:
    submit_evaluation: SubmitEvaluationUseCase
    get_job: GetJobUseCase
    process_evaluation_job: ProcessEvaluationJobUseCase
    queue: InMemoryMessageQueue


def _build_test_container() -> ApiTestContainer:
    jobs = InMemoryJobRepository()
    studies = InMemoryStudyRepository()
    queue = InMemoryMessageQueue()
    clock = SystemClock()
    logger = NullLogger()
    evaluate = EvaluateStudyUseCase(
        ingestor=_OkIngestor(),
        evaluator=_OkEvaluator(),
        repository=studies,
        logger=logger,
        clock=clock,
        scorer=ScoringService,
    )
    return ApiTestContainer(
        submit_evaluation=SubmitEvaluationUseCase(
            jobs=jobs,
            queue=queue,
            clock=clock,
            logger=logger,
            idempotency_window=timedelta(hours=24),
        ),
        get_job=GetJobUseCase(jobs=jobs, studies=studies),
        process_evaluation_job=ProcessEvaluationJobUseCase(
            evaluate=evaluate,
            jobs=jobs,
            clock=clock,
            logger=logger,
        ),
        queue=queue,
    )


@pytest.fixture
def api_client() -> TestClient:
    app = FastAPI()
    app.state.container = _build_test_container()
    app.include_router(router)
    return TestClient(app)


def test_post_evaluate_returns_202_and_publishes(api_client: TestClient) -> None:
    response = api_client.post("/api/v1/evaluate", json={"pmc_id": "PMC1"})
    assert response.status_code == 202
    body = response.json()
    assert body["job_id"]
    assert body["status_url"] == f"/api/v1/jobs/{body['job_id']}"
    assert response.headers["location"] == body["status_url"]

    container: ApiTestContainer = api_client.app.state.container  # type: ignore[attr-defined]
    assert container.queue.messages == [(body["job_id"], "PMC1")]


def test_get_job_returns_pending(api_client: TestClient) -> None:
    created = api_client.post("/api/v1/evaluate", json={"pmc_id": "PMC1"}).json()
    response = api_client.get(f"/api/v1/jobs/{created['job_id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending"
    assert body["study"] is None


@pytest.mark.anyio
async def test_evaluate_end_to_end_via_worker_path(api_client: TestClient) -> None:
    created = api_client.post("/api/v1/evaluate", json={"pmc_id": "PMC1"}).json()
    container: ApiTestContainer = api_client.app.state.container  # type: ignore[attr-defined]
    job_id, pmc_id = container.queue.messages[0]
    await container.process_evaluation_job.execute(job_id, pmc_id)

    response = api_client.get(f"/api/v1/jobs/{created['job_id']}")
    body = response.json()
    assert body["status"] == "succeeded"
    assert body["study"] is not None
    assert body["study"]["id"] == "PMC1"
