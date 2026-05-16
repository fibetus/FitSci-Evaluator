from unittest.mock import AsyncMock

import pytest

from src.adapters.ai.gemma_ollama import GemmaOllamaAdapter
from src.adapters.ai.metered_evaluator import MeteredEvaluator
from src.adapters.metrics.jsonl_metrics import JsonlMetrics
from src.domain.models.extraction import ExtractionResult


@pytest.mark.anyio
async def test_metered_evaluator_records_tokens_from_inner(tmp_path) -> None:
    metrics_path = tmp_path / "metrics.jsonl"
    inner = GemmaOllamaAdapter(base_url="http://test", model_tag="test-model")
    inner._last_llm_response = {"prompt_eval_count": 11, "eval_count": 22, "retried": False}
    inner.evaluate_text = AsyncMock(  # type: ignore[method-assign]
        return_value=ExtractionResult(
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
            primary_outcome="Y",
        )
    )

    metrics = JsonlMetrics(path=metrics_path)
    metered = MeteredEvaluator(inner, metrics=metrics, model="test-model")
    await metered.evaluate_text("paper")

    payload = metrics_path.read_text(encoding="utf-8")
    assert '"prompt_tokens": 11' in payload
    assert '"completion_tokens": 22' in payload
