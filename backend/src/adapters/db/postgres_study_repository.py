from __future__ import annotations

import time
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ...domain.errors import RepositoryError
from ...domain.models.study import QualityTier, Study, StudyTopic
from ...domain.ports.logger import LoggerPort, NullLogger
from ...domain.ports.repository import RepositoryPort
from .postgres_models import StudyRow


class PostgresStudyRepository(RepositoryPort):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        logger: LoggerPort | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._logger = logger or NullLogger()

    async def save(self, study: Study) -> None:
        started = time.perf_counter()
        document = study.model_dump(mode="json")
        values: dict[str, Any] = {
            "id": study.id,
            "pmid": study.pmid,
            "doi": study.doi,
            "topic": study.topic,
            "quality_tier": study.quality_tier,
            "score": study.score,
            "confidence": study.confidence,
            "year": study.year,
            "document": document,
        }
        stmt = (
            insert(StudyRow)
            .values(**values)
            .on_conflict_do_update(
                index_elements=[StudyRow.id],
                set_={
                    "pmid": values["pmid"],
                    "doi": values["doi"],
                    "topic": values["topic"],
                    "quality_tier": values["quality_tier"],
                    "score": values["score"],
                    "confidence": values["confidence"],
                    "year": values["year"],
                    "document": values["document"],
                    "updated_at": func.now(),
                },
            )
        )
        try:
            async with self._session_factory() as session:
                await session.execute(stmt)
                await session.commit()
        except SQLAlchemyError as exc:
            raise RepositoryError(f"Failed to save study {study.id}") from exc

        self._logger.info(
            "repository_save",
            outcome="ok",
            duration_ms=int((time.perf_counter() - started) * 1000),
            port="RepositoryPort",
            adapter="PostgresStudyRepository",
            study_id=study.id,
        )

    async def get_by_id(self, study_id: str) -> Study | None:
        try:
            async with self._session_factory() as session:
                row = await session.get(StudyRow, study_id)
        except SQLAlchemyError as exc:
            raise RepositoryError(f"Failed to load study {study_id}") from exc

        if row is None:
            return None
        return Study.model_validate(row.document)

    async def list_by(
        self,
        *,
        topic: StudyTopic | None = None,
        quality_tier: QualityTier | None = None,
        min_score: int | None = None,
        year_from: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Study]:
        stmt = select(StudyRow).order_by(StudyRow.id).limit(limit).offset(offset)
        if topic is not None:
            stmt = stmt.where(StudyRow.topic == topic)
        if quality_tier is not None:
            stmt = stmt.where(StudyRow.quality_tier == quality_tier)
        if min_score is not None:
            stmt = stmt.where(StudyRow.score >= min_score)
        if year_from is not None:
            stmt = stmt.where(StudyRow.year >= year_from)

        try:
            async with self._session_factory() as session:
                result = await session.execute(stmt)
                rows = result.scalars().all()
        except SQLAlchemyError as exc:
            raise RepositoryError("Failed to list studies") from exc

        return [Study.model_validate(row.document) for row in rows]

    async def exists(self, study_id: str) -> bool:
        stmt = select(StudyRow.id).where(StudyRow.id == study_id).limit(1)
        try:
            async with self._session_factory() as session:
                result = await session.execute(stmt)
                return result.scalar_one_or_none() is not None
        except SQLAlchemyError as exc:
            raise RepositoryError(f"Failed to check existence for {study_id}") from exc

    async def delete(self, study_id: str) -> None:
        stmt = delete(StudyRow).where(StudyRow.id == study_id)
        try:
            async with self._session_factory() as session:
                await session.execute(stmt)
                await session.commit()
        except SQLAlchemyError as exc:
            raise RepositoryError(f"Failed to delete study {study_id}") from exc
