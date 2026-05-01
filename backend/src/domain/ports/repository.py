from typing import Protocol, List, Optional
from ..models.study import Study

class RepositoryPort(Protocol):
    async def save(self, study: Study) -> None:
        """
        Persists a Study evaluation.
        """
        ...

    async def get_by_id(self, study_id: str) -> Optional[Study]:
        """
        Retrieves a saved Study by its ID.
        """
        ...

    async def list_all(self, topic: Optional[str] = None) -> List[Study]:
        """
        Lists all saved evaluations, optionally filtered by topic.
        """
        ...
