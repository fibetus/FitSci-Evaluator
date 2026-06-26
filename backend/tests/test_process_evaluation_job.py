from datetime import datetime, timezone

import pytest

from src.adapters.db.in_memory_job_repository import InMemoryJobRepository
from src.adapters.db.in_memory_repository import InMemoryStudyRepository
from src.adapters.system.clock import SystemClock
from src.application.use_cases.evaluate_study import EvaluateStudyUseCase
from src.application.use_cases.process_evaluation_job import ProcessEvaluationJobUseCase
from src.domain.errors import IngestionError
from src.domain.models.extraction import ExtractionResult
from src.domain.models.job import EvaluationJob
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


class _FailingIngestor:
    async def fetch_by_id(self, study_id: str) -> str:
        raise IngestionError("not found")

    async def search(self, query: str, limit: int = 10) -> list[str]:
        return []


@pytest.mark.anyio
async def test_process_evaluation_job_marks_succeeded() -> None:
    jobs = InMemoryJobRepository()
    studies = InMemoryStudyRepository()
    clock = SystemClock()
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    job = EvaluationJob.new(job_id="job1", pmc_id="PMC1", now=now)
    await jobs.save(job)

    evaluate = EvaluateStudyUseCase(
        ingestor=_OkIngestor(),
        evaluator=_OkEvaluator(),
        repository=studies,
        logger=NullLogger(),
        clock=clock,
        scorer=ScoringService,
    )
    processor = ProcessEvaluationJobUseCase(
        evaluate=evaluate,
        jobs=jobs,
        clock=clock,
        logger=NullLogger(),
    )

    await processor.execute("job1", "PMC1")

    updated = await jobs.get_by_id("job1")
    assert updated is not None
    assert updated.status == "succeeded"
    assert await studies.exists("PMC1") is True


@pytest.mark.anyio
async def test_process_evaluation_job_marks_failed_on_permanent_error() -> None:
    jobs = InMemoryJobRepository()
    studies = InMemoryStudyRepository()
    clock = SystemClock()
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    job = EvaluationJob.new(job_id="job2", pmc_id="PMC2", now=now)
    await jobs.save(job)

    evaluate = EvaluateStudyUseCase(
        ingestor=_FailingIngestor(),
        evaluator=_OkEvaluator(),
        repository=studies,
        logger=NullLogger(),
        clock=clock,
        scorer=ScoringService,
    )
    processor = ProcessEvaluationJobUseCase(
        evaluate=evaluate,
        jobs=jobs,
        clock=clock,
        logger=NullLogger(),
    )

    await processor.execute("job2", "PMC2")

    updated = await jobs.get_by_id("job2")
    assert updated is not None
    assert updated.status == "failed"
    assert updated.error_message is not None
