from typing import Protocol


class MetricsPort(Protocol):
    def record_llm_call(
        self,
        *,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
        schema_ok: bool,
        retried: bool,
    ) -> None:
        ...

    def record_evaluation(
        self,
        *,
        study_id: str,
        score: int,
        quality_tier: str,
        confidence: int,
        total_latency_ms: int,
    ) -> None:
        ...
