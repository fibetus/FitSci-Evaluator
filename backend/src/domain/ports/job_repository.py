from datetime import datetime, timedelta
from typing import Protocol

from ..models.job import EvaluationJob, JobStatus


class JobRepositoryPort(Protocol):
    async def save(self, job: EvaluationJob) -> None:
        ...

    async def get_by_id(self, job_id: str) -> EvaluationJob | None:
        ...

    async def find_recent_by_pmc_id(
        self,
        pmc_id: str,
        *,
        within: timedelta,
    ) -> EvaluationJob | None:
        ...

    async def update_status(
        self,
        job_id: str,
        status: JobStatus,
        *,
        error_message: str | None = None,
        updated_at: datetime,
    ) -> None:
        ...
