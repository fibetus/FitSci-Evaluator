import pytest

from src.adapters.db.in_memory_repository import InMemoryStudyRepository
from src.adapters.system.clock import SystemClock
from src.application.use_cases.evaluate_study import EvaluateStudyUseCase
from src.domain.errors import ExtractionError, IngestionError, RepositoryError
from src.domain.models.extraction import ExtractionResult
from src.domain.models.study import Study
from src.domain.ports.logger import NullLogger
from src.domain.services.scoring import ScoringService


class _RaisingIngestor:
    async def fetch_by_id(self, study_id: str) -> str:
        raise RuntimeError("network down")

    async def search(self, query: str, limit: int = 10) -> list[str]:
        return []


class _RaisingEvaluator:
    async def evaluate_text(self, text: str) -> ExtractionResult:
        raise ValueError("bad llm")


class _RaisingRepository:
    async def save(self, study: Study) -> None:
        raise KeyError("disk full")

    async def get_by_id(self, study_id: str) -> Study | None:
        return None

    async def list_by(self, **kwargs):  # type: ignore[no-untyped-def]
        return []

    async def exists(self, study_id: str) -> bool:
        return False

    async def delete(self, study_id: str) -> None:
        pass


class _MinimalEvaluator:
    async def evaluate_text(self, text: str) -> ExtractionResult:
        return ExtractionResult(
            id="PMC1",
            pmc_url="https://example.com",
            title="T",
            authors=["A"],
            journal="J",
            year=2024,
            impact_factor=1.0,
            type="rct",
            topic="protein",
            subtopic="x",
            sample_size=10,
            primary_outcome="Y",
        )


class _MinimalIngestor:
    async def fetch_by_id(self, study_id: str) -> str:
        return "paper text"

    async def search(self, query: str, limit: int = 10) -> list[str]:
        return []


def _use_case(**kwargs) -> EvaluateStudyUseCase:
    defaults = {
        "ingestor": _MinimalIngestor(),
        "evaluator": _MinimalEvaluator(),
        "repository": InMemoryStudyRepository(),
        "logger": NullLogger(),
        "clock": SystemClock(),
        "scorer": ScoringService,
    }
    defaults.update(kwargs)
    return EvaluateStudyUseCase(**defaults)


@pytest.mark.anyio
async def test_unexpected_ingestion_error_wrapped() -> None:
    use_case = _use_case(ingestor=_RaisingIngestor())
    with pytest.raises(IngestionError, match="Unexpected error during ingestion"):
        await use_case.execute("PMC1")


@pytest.mark.anyio
async def test_unexpected_evaluation_error_wrapped() -> None:
    use_case = _use_case(evaluator=_RaisingEvaluator())
    with pytest.raises(ExtractionError, match="Unexpected error during evaluation"):
        await use_case.execute("PMC1")


@pytest.mark.anyio
async def test_unexpected_persistence_error_wrapped() -> None:
    use_case = _use_case(repository=_RaisingRepository())
    with pytest.raises(RepositoryError, match="Unexpected error during persistence"):
        await use_case.execute("PMC1")
