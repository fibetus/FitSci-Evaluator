import json
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from src.adapters.ai.gemma_replay import GemmaReplayAdapter
from src.adapters.db.in_memory_repository import InMemoryStudyRepository
from src.adapters.scrapers.replay import ReplayIngestorAdapter
from src.adapters.system.clock import SystemClock
from src.adapters.system.logger import ConsoleLogger
from src.application.use_cases.evaluate_study import EvaluateStudyUseCase
from src.domain.services.scoring import ScoringService


@pytest.mark.anyio
async def test_pipeline_emits_single_correlation_id() -> None:
    fixtures_dir = Path(__file__).resolve().parents[1] / "fixtures" / "benchmark"
    buffer = StringIO()
    logger = ConsoleLogger(correlation_id="test-corr-123")

    use_case = EvaluateStudyUseCase(
        ingestor=ReplayIngestorAdapter(),
        evaluator=GemmaReplayAdapter(fixtures_dir=fixtures_dir),
        repository=InMemoryStudyRepository(logger=logger),
        logger=logger,
        clock=SystemClock(),
        scorer=ScoringService,
    )

    with patch("sys.stderr", buffer):
        await use_case.execute("PMC4848650")

    lines = [line for line in buffer.getvalue().splitlines() if line.strip()]
    assert len(lines) >= 3

    correlation_ids = set()
    for line in lines:
        payload = json.loads(line)
        correlation_ids.add(payload.get("correlation_id"))

    assert correlation_ids == {"test-corr-123"}
