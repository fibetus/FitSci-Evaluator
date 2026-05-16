from __future__ import annotations

from src.domain.ports.ingestor import IngestorPort


class ReplayIngestorAdapter(IngestorPort):
    """Embeds the PMC ID in text so GemmaReplayAdapter can load the matching fixture."""

    async def fetch_by_id(self, study_id: str) -> str:
        pmc_id = study_id.strip().upper()
        if not pmc_id.startswith("PMC"):
            pmc_id = f"PMC{pmc_id}"
        return f"fitsci-pmc-id:{pmc_id}\n\nReplay ingestor payload."

    async def search(self, query: str, limit: int = 10) -> list[str]:
        return []
