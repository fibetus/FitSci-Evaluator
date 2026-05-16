import pytest

from src.adapters.ai.gemma_replay import GemmaReplayAdapter
from src.adapters.db.in_memory_repository import InMemoryStudyRepository
from src.adapters.metrics.jsonl_metrics import JsonlMetrics
from src.adapters.scrapers.replay import ReplayIngestorAdapter
from src.adapters.system.clock import SystemClock
from src.application.use_cases.evaluate_study import EvaluateStudyUseCase
from src.domain.ports.logger import NullLogger
from src.domain.services.scoring import ScoringService


@pytest.mark.anyio
async def test_execute_records_evaluation_metric(tmp_path) -> None:
    fixtures_dir = tmp_path
    (fixtures_dir / "PMC1.json").write_text(
        '{"id":"PMC1","pmc_url":"https://example.com","title":"T","authors":["A"],'
        '"journal":"J","year":2024,"impact_factor":1.0,"type":"rct","topic":"protein",'
        '"subtopic":"x","sample_size":10,"primary_outcome":"Y","flags":{}}',
        encoding="utf-8",
    )
    metrics_path = tmp_path / "metrics.jsonl"

    use_case = EvaluateStudyUseCase(
        ingestor=ReplayIngestorAdapter(),
        evaluator=GemmaReplayAdapter(fixtures_dir=fixtures_dir),
        repository=InMemoryStudyRepository(),
        logger=NullLogger(),
        clock=SystemClock(),
        scorer=ScoringService,
        metrics=JsonlMetrics(path=metrics_path),
    )

    await use_case.execute("PMC1")
    assert '"event": "evaluation"' in metrics_path.read_text(encoding="utf-8")
