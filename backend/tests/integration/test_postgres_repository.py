import os

import pytest
from testcontainers.postgres import PostgresContainer

from src.adapters.db.engine import create_engine, create_session_factory, init_schema
from src.adapters.db.postgres_study_repository import PostgresStudyRepository
from src.config.settings import Settings
from src.domain.models.study import Study

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("FITSCI_INTEGRATION") != "1",
        reason="Set FITSCI_INTEGRATION=1 to run Postgres integration tests",
    ),
]


def _study(study_id: str, **kwargs: object) -> Study:
    defaults: dict[str, object] = {
        "id": study_id,
        "pmc_url": "https://example.com",
        "title": "T",
        "authors": ["A"],
        "journal": "J",
        "year": 2024,
        "impact_factor": 1.0,
        "type": "rct",
        "topic": "protein",
        "subtopic": "x",
        "sample_size": 10,
        "primary_outcome": "Y",
        "score": 8,
        "confidence": 90,
        "quality_tier": "high",
    }
    defaults.update(kwargs)
    return Study(**defaults)  # type: ignore[arg-type]


@pytest.fixture
def postgres_settings() -> Settings:
    with PostgresContainer("postgres:16-alpine") as postgres:
        sync_url = postgres.get_connection_url()
        async_url = sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1).replace(
            "postgresql://", "postgresql+asyncpg://", 1
        )
        yield Settings(
            deployment="local",
            postgres_dsn=async_url,
            postgres_sync_dsn=sync_url.replace("postgresql://", "postgresql+psycopg://", 1),
            rabbitmq_url="amqp://guest:guest@localhost:5672/",
            ollama_base_url="http://localhost:11434",
            gemma_model_tag="gemma4:12b-q4_k_m",
            log_level="INFO",
            rate_limit_per_minute=30,
            ncbi_api_key=None,
            rabbitmq_evaluation_queue="fitsci.evaluation.jobs",
            evaluation_idempotency_hours=24,
        )


@pytest.mark.anyio
async def test_postgres_repository_roundtrip(postgres_settings: Settings) -> None:
    engine = create_engine(postgres_settings)
    await init_schema(engine)
    factory = create_session_factory(engine)
    repo = PostgresStudyRepository(factory)

    original = _study("PMC99999")
    await repo.save(original)

    loaded = await repo.get_by_id("PMC99999")
    assert loaded is not None
    assert loaded.model_dump() == original.model_dump()

    listed = await repo.list_by(topic="protein", min_score=5, year_from=2020)
    assert [study.id for study in listed] == ["PMC99999"]

    assert await repo.exists("PMC99999") is True
    await repo.delete("PMC99999")
    assert await repo.exists("PMC99999") is False

    await engine.dispose()
