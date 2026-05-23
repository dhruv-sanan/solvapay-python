"""Tests for AsyncInMemorySeenEventCache atomicity and correctness."""

from __future__ import annotations

import asyncio

from solvapay.webhooks.replay import AsyncInMemorySeenEventCache


async def test_first_claim_returns_true() -> None:
    cache = AsyncInMemorySeenEventCache()
    assert await cache.try_claim("evt_1", 600) is True


async def test_duplicate_claim_returns_false() -> None:
    cache = AsyncInMemorySeenEventCache()
    assert await cache.try_claim("evt_1", 600) is True
    assert await cache.try_claim("evt_1", 600) is False


async def test_different_events_both_claimed() -> None:
    cache = AsyncInMemorySeenEventCache()
    assert await cache.try_claim("evt_a", 600) is True
    assert await cache.try_claim("evt_b", 600) is True


async def test_expired_event_can_be_reclaimed() -> None:
    cache = AsyncInMemorySeenEventCache()
    await cache.try_claim("evt_expire", ttl_seconds=0)
    # Manually expire by back-dating the entry
    import time

    cache._store["evt_expire"] = time.time() - 1
    assert await cache.try_claim("evt_expire", 600) is True


async def test_concurrent_claims_exactly_one_wins() -> None:
    """10 concurrent tasks race to claim the same event ID — exactly one must win."""
    cache = AsyncInMemorySeenEventCache()
    results: list[bool] = []

    async def claim() -> None:
        result = await cache.try_claim("evt_race", 600)
        results.append(result)

    await asyncio.gather(*[claim() for _ in range(10)])
    assert results.count(True) == 1
    assert results.count(False) == 9
