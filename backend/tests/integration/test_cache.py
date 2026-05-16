import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.adapters.ai.cached_evaluator import CachedEvaluator
from src.adapters.ai.gemma_ollama import GemmaOllamaAdapter
from src.adapters.cache.in_memory_cache import InMemoryCache
from src.domain.models.extraction import ExtractionResult


@pytest.fixture
def valid_study_json() -> dict:
    return {
        "id": "PMC123",
        "pmc_url": "http://example.com",
        "title": "Test Title",
        "authors": ["Author 1"],
        "journal": "Test Journal",
        "year": 2024,
        "impact_factor": 5.0,
        "type": "rct",
        "topic": "hypertrophy",
        "subtopic": "muscle",
        "sample_size": 20,
        "population": {},
        "primary_outcome": "growth",
        "flags": {},
    }


@pytest.mark.anyio
async def test_evaluate_text_uses_cache_on_second_call(valid_study_json: dict) -> None:
    base = GemmaOllamaAdapter(base_url="http://test", model_tag="test-model")
    adapter = CachedEvaluator(base, InMemoryCache(), model_tag="test-model")

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "response": json.dumps(valid_study_json),
        "prompt_eval_count": 10,
        "eval_count": 20,
    }

    mock_client_instance = AsyncMock()
    mock_client_instance.post.return_value = mock_response

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        first = await adapter.evaluate_text("Same paper body")
        second = await adapter.evaluate_text("Same paper body")

    assert isinstance(first, ExtractionResult)
    assert isinstance(second, ExtractionResult)
    assert mock_client_instance.post.call_count == 1
