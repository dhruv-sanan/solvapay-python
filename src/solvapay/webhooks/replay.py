"""Replay-attack protection via atomic try_claim (HLD V1.7 WP1)."""

from __future__ import annotations

import asyncio
import threading
import time
from typing import Protocol, runtime_checkable


@runtime_checkable
class SeenEventCache(Protocol):
    """Atomic event-ID deduplication cache (HLD WP1).

    try_claim MUST be atomic: claim-check and claim-set happen together
    under one lock. Never call seen() + remember() separately.
    """

    def try_claim(self, event_id: str, ttl_seconds: int) -> bool:
        """Return True and claim event_id if not seen; return False if already claimed."""
        ...


class InMemorySeenEventCache:
    """Sync in-memory cache. Thread-safe via threading.Lock (HLD WP1 atomic)."""

    def __init__(self, maxsize: int = 10_000) -> None:
        self._maxsize = maxsize
        self._lock = threading.Lock()
        self._store: dict[str, float] = {}

    def try_claim(self, event_id: str, ttl_seconds: int) -> bool:
        now = time.time()
        with self._lock:
            # Evict expired entries to bound memory
            if len(self._store) >= self._maxsize:
                cutoff = now
                self._store = {k: v for k, v in self._store.items() if v > cutoff}

            if event_id in self._store and self._store[event_id] > now:
                return False
            self._store[event_id] = now + ttl_seconds
            return True


@runtime_checkable
class AsyncSeenEventCache(Protocol):
    """Async variant of SeenEventCache for use in async webhook pipelines (HLD WP1)."""

    async def try_claim(self, event_id: str, ttl_seconds: int) -> bool:
        """Return True and claim event_id if not seen; return False if already claimed."""
        ...


class AsyncInMemorySeenEventCache:
    """Async in-memory cache. asyncio.Lock for async pipelines (HLD WP1 atomic)."""

    def __init__(self, maxsize: int = 10_000) -> None:
        self._maxsize = maxsize
        self._lock = asyncio.Lock()
        self._store: dict[str, float] = {}

    async def try_claim(self, event_id: str, ttl_seconds: int) -> bool:
        now = time.time()
        async with self._lock:
            # Evict expired entries to bound memory
            if len(self._store) >= self._maxsize:
                cutoff = now
                self._store = {k: v for k, v in self._store.items() if v > cutoff}

            if event_id in self._store and self._store[event_id] > now:
                return False
            self._store[event_id] = now + ttl_seconds
            return True
