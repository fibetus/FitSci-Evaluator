from datetime import datetime, timedelta, timezone

import pytest

from src.adapters.broker.in_memory_queue import InMemoryMessageQueue
from src.adapters.db.in_memory_job_repository import InMemoryJobRepository
from src.adapters.system.clock import SystemClock
from src.application.use_cases.submit_evaluation import SubmitEvaluationUseCase
from src.domain.ports.logger import NullLogger


@pytest.mark.anyio
async def test_submit_evaluation_creates_job_and_publishes() -> None:
    jobs = InMemoryJobRepository()
    queue = InMemoryMessageQueue()
    clock = SystemClock()
    use_case = SubmitEvaluationUseCase(
        jobs=jobs,
        queue=queue,
        clock=clock,
        logger=NullLogger(),
    )

    job = await use_case.execute("PMC12345")

    assert job.status == "pending"
    assert job.pmc_id == "PMC12345"
    assert queue.messages == [(job.id, "PMC12345")]
    stored = await jobs.get_by_id(job.id)
    assert stored is not None


@pytest.mark.anyio
async def test_submit_evaluation_idempotent_within_window() -> None:
    jobs = InMemoryJobRepository()
    queue = InMemoryMessageQueue()
    fixed_now = datetime.now(timezone.utc)

    class _FixedClock:
        def now(self) -> datetime:
            return fixed_now

    use_case = SubmitEvaluationUseCase(
        jobs=jobs,
        queue=queue,
        clock=_FixedClock(),  # type: ignore[arg-type]
        logger=NullLogger(),
        idempotency_window=timedelta(hours=24),
    )

    first = await use_case.execute("PMC99999")
    second = await use_case.execute("PMC99999")

    assert first.id == second.id
    assert len(queue.messages) == 1
