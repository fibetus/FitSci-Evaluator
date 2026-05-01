from typing import Protocol, List

class IngestorPort(Protocol):
    async def fetch_by_id(self, study_id: str) -> str:
        """
        Fetches raw text/XML from a source (e.g. PMC) by its ID.
        """
        ...

    async def search(self, query: str, limit: int = 10) -> List[str]:
        """
        Searches for publications and returns a list of IDs.
        """
        ...
