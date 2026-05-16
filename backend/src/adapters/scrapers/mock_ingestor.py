from __future__ import annotations

from src.domain.ports.ingestor import IngestorPort


class MockIngestorAdapter(IngestorPort):
    """Returns deterministic placeholder text keyed by PMC ID for offline CLI runs."""

    async def fetch_by_id(self, study_id: str) -> str:
        pmc_id = study_id.strip().upper()
        if not pmc_id.startswith("PMC"):
            pmc_id = f"PMC{pmc_id}"
        return f"fitsci-pmc-id:{pmc_id}\n\nOffline mock ingestor payload."

    async def search(self, query: str, limit: int = 10) -> list[str]:
        return []
