from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ...domain.errors import RepositoryError
from ...domain.models.job import EvaluationJob, JobStatus
from ...domain.ports.job_repository import JobRepositoryPort
from .postgres_models import EvaluationJobRow


class PostgresJobRepository(JobRepositoryPort):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def save(self, job: EvaluationJob) -> None:
        row = EvaluationJobRow(
            id=job.id,
            pmc_id=job.pmc_id,
            status=job.status,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )
        try:
            async with self._session_factory() as session:
                session.add(row)
                await session.commit()
        except SQLAlchemyError as exc:
            raise RepositoryError(f"Failed to save job {job.id}") from exc

    async def get_by_id(self, job_id: str) -> EvaluationJob | None:
        try:
            async with self._session_factory() as session:
                row = await session.get(EvaluationJobRow, job_id)
        except SQLAlchemyError as exc:
            raise RepositoryError(f"Failed to load job {job_id}") from exc
        if row is None:
            return None
        return _row_to_job(row)

    async def find_recent_by_pmc_id(
        self,
        pmc_id: str,
        *,
        within: timedelta,
    ) -> EvaluationJob | None:
        cutoff = datetime.now(timezone.utc) - within
        stmt = (
            select(EvaluationJobRow)
            .where(EvaluationJobRow.pmc_id == pmc_id)
            .where(EvaluationJobRow.created_at >= cutoff)
            .order_by(EvaluationJobRow.created_at.desc())
            .limit(1)
        )
        try:
            async with self._session_factory() as session:
                result = await session.execute(stmt)
                row = result.scalar_one_or_none()
        except SQLAlchemyError as exc:
            raise RepositoryError(f"Failed to find recent job for {pmc_id}") from exc
        if row is None:
            return None
        return _row_to_job(row)

    async def update_status(
        self,
        job_id: str,
        status: JobStatus,
        *,
        error_message: str | None = None,
        updated_at: datetime,
    ) -> None:
        stmt = (
            update(EvaluationJobRow)
            .where(EvaluationJobRow.id == job_id)
            .values(status=status, error_message=error_message, updated_at=updated_at)
        )
        try:
            async with self._session_factory() as session:
                existing = await session.get(EvaluationJobRow, job_id)
                if existing is None:
                    raise RepositoryError(f"Job {job_id} not found")
                await session.execute(stmt)
                await session.commit()
        except SQLAlchemyError as exc:
            raise RepositoryError(f"Failed to update job {job_id}") from exc


def _row_to_job(row: EvaluationJobRow) -> EvaluationJob:
    return EvaluationJob(
        id=row.id,
        pmc_id=row.pmc_id,
        status=row.status,
        error_message=row.error_message,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
