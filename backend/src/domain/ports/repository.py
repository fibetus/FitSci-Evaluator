from typing import Protocol

from ..models.study import QualityTier, Study, StudyTopic


class RepositoryPort(Protocol):
    async def save(self, study: Study) -> None:
        """
        Persists a Study evaluation.
        """
        ...

    async def get_by_id(self, study_id: str) -> Study | None:
        """
        Retrieves a saved Study by its ID.
        """
        ...

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
        """
        Lists saved evaluations with promoted-column filters.
        """
        ...

    async def exists(self, study_id: str) -> bool:
        """
        Returns whether a Study evaluation already exists.
        """
        ...

    async def delete(self, study_id: str) -> None:
        """
        Deletes a saved Study evaluation by ID.
        """
        ...
