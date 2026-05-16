from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.domain.ports.metrics import MetricsPort


class JsonlMetrics(MetricsPort):
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path("metrics.jsonl")

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
        self._append(
            {
                "event": "llm_call",
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "latency_ms": latency_ms,
                "schema_ok": schema_ok,
                "retried": retried,
            }
        )

    def record_evaluation(
        self,
        *,
        study_id: str,
        score: int,
        quality_tier: str,
        confidence: int,
        total_latency_ms: int,
    ) -> None:
        self._append(
            {
                "event": "evaluation",
                "study_id": study_id,
                "score": score,
                "quality_tier": quality_tier,
                "confidence": confidence,
                "total_latency_ms": total_latency_ms,
            }
        )

    def _append(self, payload: dict[str, Any]) -> None:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
