import pytest

from src.adapters.ai.mock import MockEvaluatorAdapter
from src.adapters.db.in_memory_repository import InMemoryStudyRepository
from src.adapters.metrics.jsonl_metrics import JsonlMetrics
from src.adapters.scrapers.mock_ingestor import MockIngestorAdapter
from src.adapters.system.clock import SystemClock
from src.application.use_cases.evaluate_study import EvaluateStudyUseCase
from src.domain.ports.logger import NullLogger
from src.domain.services.scoring import ScoringService


@pytest.mark.anyio
async def test_mock_adapters_drive_use_case(tmp_path) -> None:
    metrics_path = tmp_path / "metrics.jsonl"
    use_case = EvaluateStudyUseCase(
        ingestor=MockIngestorAdapter(),
        evaluator=MockEvaluatorAdapter(),
        repository=InMemoryStudyRepository(),
        logger=NullLogger(),
        clock=SystemClock(),
        scorer=ScoringService,
        metrics=JsonlMetrics(path=metrics_path),
    )

    study = await use_case.execute("PMC12345")
    assert study.id == "PMC12345"
    assert study.score > 0
    assert metrics_path.read_text(encoding="utf-8").count('"event": "evaluation"') == 1


@pytest.mark.anyio
async def test_mock_ingestor_search_returns_empty() -> None:
    ingestor = MockIngestorAdapter()
    assert await ingestor.search("hypertrophy") == []
