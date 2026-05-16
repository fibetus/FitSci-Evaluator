from __future__ import annotations

import json
import re
from pathlib import Path

from src.domain.errors import ExtractionError
from src.domain.models.extraction import ExtractionResult
from src.domain.ports.evaluator import EvaluatorPort

_PMC_ID_PATTERN = re.compile(r"fitsci-pmc-id:(PMC\d+)", re.IGNORECASE)


class GemmaReplayAdapter(EvaluatorPort):
    """Returns gold fixture JSON for CI and integration tests (no live Ollama)."""

    def __init__(self, fixtures_dir: Path | None = None) -> None:
        self._fixtures_dir = fixtures_dir or (
            Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "benchmark"
        )

    async def evaluate_text(self, text: str) -> ExtractionResult:
        match = _PMC_ID_PATTERN.search(text)
        if not match:
            raise ExtractionError("Replay adapter could not resolve PMC ID from ingested text.")

        pmc_id = match.group(1).upper()
        fixture_path = self._fixtures_dir / f"{pmc_id}.json"
        if not fixture_path.exists():
            raise ExtractionError(f"No replay fixture for {pmc_id} at {fixture_path}")

        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        return ExtractionResult.from_llm_json(payload)
