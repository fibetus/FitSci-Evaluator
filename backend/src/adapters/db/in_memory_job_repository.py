from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ...domain.models.job import EvaluationJob, JobStatus
from ...domain.ports.job_repository import JobRepositoryPort


class InMemoryJobRepository(JobRepositoryPort):
    def __init__(self) -> None:
        self._jobs: dict[str, EvaluationJob] = {}

    async def save(self, job: EvaluationJob) -> None:
        self._jobs[job.id] = job

    async def get_by_id(self, job_id: str) -> EvaluationJob | None:
        return self._jobs.get(job_id)

    async def find_recent_by_pmc_id(
        self,
        pmc_id: str,
        *,
        within: timedelta,
    ) -> EvaluationJob | None:
        cutoff = datetime.now(timezone.utc) - within
        matches = [
            job
            for job in self._jobs.values()
            if job.pmc_id == pmc_id and job.created_at >= cutoff
        ]
        if not matches:
            return None
        return max(matches, key=lambda job: job.created_at)

    async def update_status(
        self,
        job_id: str,
        status: JobStatus,
        *,
        error_message: str | None = None,
        updated_at: datetime,
    ) -> None:
        job = self._jobs.get(job_id)
        if job is None:
            return
        self._jobs[job_id] = job.model_copy(
            update={
                "status": status,
                "error_message": error_message,
                "updated_at": updated_at,
            }
        )
