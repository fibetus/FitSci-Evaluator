import pytest

from src.adapters.db.in_memory_repository import InMemoryStudyRepository
from src.domain.models.study import Study


def _study(study_id: str, **kwargs) -> Study:
    defaults = {
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
    }
    defaults.update(kwargs)
    return Study(**defaults)


@pytest.mark.anyio
async def test_repository_list_and_delete() -> None:
    repo = InMemoryStudyRepository()
    await repo.save(_study("PMC1", topic="protein", score=8, quality_tier="high", year=2024))
    await repo.save(_study("PMC2", topic="creatine", score=3, quality_tier="rejected", year=2019))

    listed = await repo.list_by(topic="protein", min_score=5, year_from=2020, limit=10)
    assert [study.id for study in listed] == ["PMC1"]

    assert await repo.get_by_id("PMC1") is not None
    await repo.delete("PMC1")
    assert await repo.exists("PMC1") is False
