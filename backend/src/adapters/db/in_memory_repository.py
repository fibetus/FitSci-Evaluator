from typing import Dict, List, Optional

from ...domain.models.study import QualityTier, Study, StudyTopic
from ...domain.ports.repository import RepositoryPort


class InMemoryStudyRepository(RepositoryPort):
    def __init__(self) -> None:
        self._storage: Dict[str, Study] = {}

    async def save(self, study: Study) -> None:
        self._storage[study.id] = study

    async def get_by_id(self, study_id: str) -> Optional[Study]:
        return self._storage.get(study_id)

    async def list_by(
        self,
        *,
        topic: Optional[StudyTopic] = None,
        quality_tier: Optional[QualityTier] = None,
        min_score: Optional[int] = None,
        year_from: Optional[int] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Study]:
        results = list(self._storage.values())

        if topic:
            results = [s for s in results if s.topic == topic]
        if quality_tier:
            results = [s for s in results if s.quality_tier == quality_tier]
        if min_score is not None:
            results = [s for s in results if s.score >= min_score]
        if year_from is not None:
            results = [s for s in results if s.year >= year_from]

        # Sort by ID to keep results deterministic
        results.sort(key=lambda s: s.id)

        return results[offset : offset + limit]

    async def exists(self, study_id: str) -> bool:
        return study_id in self._storage

    async def delete(self, study_id: str) -> None:
        self._storage.pop(study_id, None)
