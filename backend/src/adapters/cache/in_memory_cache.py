from __future__ import annotations

import time
from dataclasses import dataclass

from src.domain.ports.cache import CachePort


@dataclass
class _CacheEntry:
    value: str
    expires_at: float | None


class InMemoryCache(CachePort):
    def __init__(self) -> None:
        self._store: dict[str, _CacheEntry] = {}

    async def get(self, key: str) -> str | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.expires_at is not None and time.monotonic() > entry.expires_at:
            del self._store[key]
            return None
        return entry.value

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        expires_at = time.monotonic() + ttl_seconds if ttl_seconds is not None else None
        self._store[key] = _CacheEntry(value=value, expires_at=expires_at)
