"""Tests: max_clock_skew_seconds and replay_ttl_seconds operate independently (HLD WP2)."""

from __future__ import annotations

import hashlib
import hmac
import json
import time

import pytest

from solvapay.exceptions import SolvaPayError
from solvapay.webhooks.pipeline import WebhookPipeline
from solvapay.webhooks.replay import InMemorySeenEventCache

SECRET = "whsec_two_knobs"


def _sign_at(body: str, ts: int, secret: str = SECRET) -> str:
    sig = hmac.new(secret.encode(), f"{ts}.{body}".encode(), hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def test_within_skew_but_replayed() -> None:
    """Fresh timestamp (within clock skew) but event already claimed → replay blocked."""
    body = json.dumps({"id": "evt_replay", "type": "test"}).encode()
    ts = int(time.time())
    sig = _sign_at(body.decode(), ts)

    cache = InMemorySeenEventCache()
    pipeline = WebhookPipeline([SECRET], max_clock_skew_seconds=300, replay_ttl_seconds=600, seen_cache=cache)

    pipeline.process(body, sig)  # first: OK
    with pytest.raises(SolvaPayError, match="already processed"):
        pipeline.process(body, sig)  # second: replay blocked


def test_stale_timestamp_fails_regardless_of_replay_cache() -> None:
    """Clock skew check fires before replay check."""
    ts = int(time.time()) - 400
    body = json.dumps({"id": "evt_stale", "type": "test"}).encode()
    sig = _sign_at(body.decode(), ts)

    pipeline = WebhookPipeline([SECRET], max_clock_skew_seconds=300, replay_ttl_seconds=6000)
    with pytest.raises(SolvaPayError, match="clock skew"):
        pipeline.process(body, sig)


def test_two_knobs_are_separate_params() -> None:
    pipeline = WebhookPipeline(
        [SECRET],
        max_clock_skew_seconds=10,
        replay_ttl_seconds=999,
    )
    assert pipeline._max_clock_skew_seconds == 10
    assert pipeline._replay_ttl_seconds == 999
