from __future__ import annotations

from dataclasses import dataclass

from src.domain.errors import JobNotFoundError
from src.domain.models.job import EvaluationJob
from src.domain.models.study import Study
from src.domain.ports.job_repository import JobRepositoryPort
from src.domain.ports.repository import RepositoryPort


@dataclass(frozen=True)
class JobWithStudy:
    job: EvaluationJob
    study: Study | None


@dataclass(frozen=True)
class GetJobUseCase:
    jobs: JobRepositoryPort
    studies: RepositoryPort

    async def execute(self, job_id: str) -> JobWithStudy:
        job = await self.jobs.get_by_id(job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id} not found")

        study: Study | None = None
        if job.status == "succeeded":
            study = await self.studies.get_by_id(job.pmc_id)

        return JobWithStudy(job=job, study=study)
