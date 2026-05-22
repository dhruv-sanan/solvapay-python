"""Tests: WebhookPipeline composition and happy path."""

from __future__ import annotations

import hashlib
import hmac
import json
import time

import pytest

from solvapay.exceptions import SolvaPayError
from solvapay.webhooks.pipeline import WebhookPipeline

SECRET = "whsec_test_secret"
EVENT = {"id": "evt_001", "type": "payment.succeeded", "data": {}}


def _sign(body: str, secret: str = SECRET) -> str:
    ts = int(time.time())
    sig = hmac.new(secret.encode(), f"{ts}.{body}".encode(), hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def test_pipeline_happy_path() -> None:
    body = json.dumps(EVENT).encode()
    sig = _sign(body.decode())
    pipeline = WebhookPipeline([SECRET])
    envelope = pipeline.process(body, sig)
    assert envelope.event_id == "evt_001"
    assert envelope.event["type"] == "payment.succeeded"


def test_pipeline_rejects_bad_secret() -> None:
    body = json.dumps(EVENT).encode()
    sig = _sign(body.decode(), secret="wrong_secret")
    pipeline = WebhookPipeline([SECRET])
    with pytest.raises(SolvaPayError, match="mismatch"):
        pipeline.process(body, sig)


def test_pipeline_rejects_stale_timestamp() -> None:
    ts = int(time.time()) - 400
    body = json.dumps(EVENT).encode()
    sig_val = hmac.new(
        SECRET.encode(), f"{ts}.{body.decode()}".encode(), hashlib.sha256
    ).hexdigest()
    sig = f"t={ts},v1={sig_val}"
    pipeline = WebhookPipeline([SECRET], max_clock_skew_seconds=300)
    with pytest.raises(SolvaPayError, match="clock skew"):
        pipeline.process(body, sig)


def test_pipeline_requires_secrets() -> None:
    with pytest.raises(ValueError):
        WebhookPipeline([])


def test_pipeline_dispatcher_called() -> None:
    received = []
    body = json.dumps(EVENT).encode()
    sig = _sign(body.decode())
    pipeline = WebhookPipeline([SECRET], dispatcher=received.append)
    pipeline.process(body, sig)
    assert len(received) == 1
    assert received[0]["id"] == "evt_001"
