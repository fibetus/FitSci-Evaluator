from __future__ import annotations

import time
from typing import Any, Protocol, runtime_checkable

from src.domain.models.extraction import ExtractionResult
from src.domain.ports.evaluator import EvaluatorPort
from src.domain.ports.metrics import MetricsPort


@runtime_checkable
class SupportsLlmMetrics(Protocol):
    @property
    def last_llm_response(self) -> dict[str, Any] | None:
        ...


class MeteredEvaluator:
    """Decorator: records latency and token usage for each evaluate_text call."""

    def __init__(
        self,
        inner: EvaluatorPort,
        metrics: MetricsPort,
        *,
        model: str,
    ) -> None:
        self._inner = inner
        self._metrics = metrics
        self._model = model

    async def evaluate_text(self, text: str) -> ExtractionResult:
        started = time.perf_counter()
        retried = False
        try:
            result = await self._inner.evaluate_text(text)
        except Exception:
            latency_ms = int((time.perf_counter() - started) * 1000)
            self._metrics.record_llm_call(
                model=self._model,
                prompt_tokens=0,
                completion_tokens=0,
                latency_ms=latency_ms,
                schema_ok=False,
                retried=retried,
            )
            raise

        latency_ms = int((time.perf_counter() - started) * 1000)
        llm_data: dict[str, Any] = {}
        if isinstance(self._inner, SupportsLlmMetrics):
            llm_data = self._inner.last_llm_response or {}
        retried = bool(llm_data.get("retried", False))

        self._metrics.record_llm_call(
            model=self._model,
            prompt_tokens=int(llm_data.get("prompt_eval_count", 0)),
            completion_tokens=int(llm_data.get("eval_count", 0)),
            latency_ms=latency_ms,
            schema_ok=True,
            retried=retried,
        )
        return result
