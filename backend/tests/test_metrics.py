from pathlib import Path

from src.adapters.metrics.jsonl_metrics import JsonlMetrics


def test_jsonl_metrics_writes_llm_and_evaluation_events(tmp_path: Path) -> None:
    path = tmp_path / "metrics.jsonl"
    metrics = JsonlMetrics(path=path)

    metrics.record_llm_call(
        model="test-model",
        prompt_tokens=10,
        completion_tokens=20,
        latency_ms=100,
        schema_ok=True,
        retried=False,
    )
    metrics.record_evaluation(
        study_id="PMC1",
        score=8,
        quality_tier="high",
        confidence=90,
        total_latency_ms=250,
    )

    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert '"event": "llm_call"' in lines[0]
    assert '"event": "evaluation"' in lines[1]
