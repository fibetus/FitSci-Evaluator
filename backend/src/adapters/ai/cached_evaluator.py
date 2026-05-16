from __future__ import annotations

import hashlib

from src.domain.models.extraction import ExtractionResult
from src.domain.ports.cache import CachePort
from src.domain.ports.evaluator import EvaluatorPort


class CachedEvaluator:
    """Decorator: caches LLM JSON responses keyed by model tag + input text."""

    def __init__(
        self,
        inner: EvaluatorPort,
        cache: CachePort,
        *,
        model_tag: str,
        ttl_seconds: int = 86_400,
    ) -> None:
        self._inner = inner
        self._cache = cache
        self._model_tag = model_tag
        self._ttl_seconds = ttl_seconds

    def _cache_key(self, text: str) -> str:
        prompt_hash = hashlib.sha256(text.encode()).hexdigest()
        material = f"{self._model_tag}:{prompt_hash}".encode()
        return hashlib.sha256(material).hexdigest()

    async def evaluate_text(self, text: str) -> ExtractionResult:
        key = self._cache_key(text)
        cached = await self._cache.get(key)
        if cached is not None:
            return ExtractionResult.model_validate_json(cached)

        result = await self._inner.evaluate_text(text)
        await self._cache.set(
            key,
            result.model_dump_json(),
            ttl_seconds=self._ttl_seconds,
        )
        return result
