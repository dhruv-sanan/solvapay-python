"""Tests: InMemorySeenEventCache.try_claim atomicity (HLD V1.7 WP1)."""

from __future__ import annotations

import threading

from solvapay.webhooks.replay import InMemorySeenEventCache


def test_first_claim_returns_true() -> None:
    cache = InMemorySeenEventCache()
    assert cache.try_claim("evt_001", 600) is True


def test_second_claim_returns_false() -> None:
    cache = InMemorySeenEventCache()
    cache.try_claim("evt_001", 600)
    assert cache.try_claim("evt_001", 600) is False


def test_different_ids_both_claim() -> None:
    cache = InMemorySeenEventCache()
    assert cache.try_claim("evt_001", 600) is True
    assert cache.try_claim("evt_002", 600) is True


def test_concurrent_only_one_wins() -> None:
    cache = InMemorySeenEventCache()
    results: list[bool] = []
    lock = threading.Lock()

    def claim() -> None:
        result = cache.try_claim("evt_concurrent", 600)
        with lock:
            results.append(result)

    threads = [threading.Thread(target=claim) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results.count(True) == 1
    assert results.count(False) == 19


def test_expired_entry_can_be_reclaimed() -> None:
    cache = InMemorySeenEventCache()
    # Claim with ttl=0 to simulate immediate expiry
    cache.try_claim("evt_exp", 0)
    import time

    time.sleep(0.01)
    assert cache.try_claim("evt_exp", 600) is True
