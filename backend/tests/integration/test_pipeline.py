from pathlib import Path

import pytest

from src.adapters.ai.gemma_replay import GemmaReplayAdapter
from src.adapters.db.in_memory_repository import InMemoryStudyRepository
from src.adapters.scrapers.replay import ReplayIngestorAdapter
from src.adapters.system.clock import SystemClock
from src.application.use_cases.evaluate_study import EvaluateStudyUseCase
from src.domain.models.study import Study
from src.domain.ports.logger import NullLogger
from src.domain.services.scoring import ScoringService

FIXTURE_IDS = [
    "PMC4848650",
    "PMC4558471",
    "PMC4022420",
    "PMC4941165",
    "PMC2901358",
]


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "benchmark"


@pytest.fixture
def use_case(fixtures_dir: Path) -> EvaluateStudyUseCase:
    return EvaluateStudyUseCase(
        ingestor=ReplayIngestorAdapter(),
        evaluator=GemmaReplayAdapter(fixtures_dir=fixtures_dir),
        repository=InMemoryStudyRepository(),
        logger=NullLogger(),
        clock=SystemClock(),
        scorer=ScoringService,
    )


@pytest.mark.anyio
@pytest.mark.parametrize("pmc_id", FIXTURE_IDS)
async def test_pipeline_round_trip(pmc_id: str, use_case: EvaluateStudyUseCase) -> None:
    study = await use_case.execute(pmc_id)

    Study.model_validate_json(study.model_dump_json())
    assert await use_case.repository.exists(pmc_id)
    assert study.id == pmc_id
    assert study.score >= 0
    assert study.quality_tier in {"high", "moderate", "rejected"}
