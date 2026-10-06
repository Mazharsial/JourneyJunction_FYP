"""
Tiny in-process TTL cache for hot, rarely-changing reference data (countries,
cities, currencies, visa lookups, plans). Caches serialized Pydantic objects
(session-independent), never ORM rows. Invalidated on admin mutations and by TTL.

Per-process (fine for a single worker / dev). A shared Redis cache is the drop-in
upgrade for multi-worker production.
"""
from __future__ import annotations

import time
from typing import Any

_DEFAULT_TTL = 300  # seconds


class TTLCache:
    def __init__(self, ttl: int = _DEFAULT_TTL):
        self._ttl = ttl
        self._store: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if not entry:
            return None
        value, expires = entry
        if time.monotonic() > expires:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        self._store[key] = (value, time.monotonic() + (ttl or self._ttl))

    def clear(self) -> None:
        self._store.clear()


cache = TTLCache()
