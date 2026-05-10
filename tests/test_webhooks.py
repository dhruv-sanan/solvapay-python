"""Tests for webhook signature verification."""
from __future__ import annotations

import hashlib
import hmac
import json
import time

import pytest

from solvapay import SolvaPayError
from solvapay.webhooks import verify_webhook

SECRET = "whsec_test_secret"


def _sign(body: str, ts: int | None = None, secret: str = SECRET) -> tuple[str, int]:
    ts = ts or int(time.time())
    h = hmac.new(secret.encode(), f"{ts}.{body}".encode(), hashlib.sha256).hexdigest()
    return f"t={ts},v1={h}", ts


def test_valid_signature_roundtrip() -> None:
    body = json.dumps({
        "id": "evt_1",
        "type": "purchase.created",
        "created": 1,
        "api_version": "2025-10-01",
        "data": {"object": {"id": "pur_1"}, "previous_attributes": None},
        "livemode": False,
        "request": {"id": None, "idempotency_key": None},
    })
    sig, _ = _sign(body)
    event = verify_webhook(body=body, signature=sig, secret=SECRET)
    assert event["type"] == "purchase.created"


def test_expired_timestamp_rejected() -> None:
    body = '{"type": "purchase.created"}'
    old_ts = int(time.time()) - 600
    sig, _ = _sign(body, ts=old_ts)
    with pytest.raises(SolvaPayError, match="too old"):
        verify_webhook(body=body, signature=sig, secret=SECRET)


def test_wrong_signature_rejected() -> None:
    body = '{"type": "purchase.created"}'
    sig, _ = _sign(body, secret="whsec_other_secret")
    with pytest.raises(SolvaPayError, match="mismatch"):
        verify_webhook(body=body, signature=sig, secret=SECRET)


def test_tampered_body_rejected() -> None:
    original = '{"type": "purchase.created"}'
    sig, _ = _sign(original)
    tampered = '{"type": "purchase.cancelled"}'
    with pytest.raises(SolvaPayError, match="mismatch"):
        verify_webhook(body=tampered, signature=sig, secret=SECRET)


def test_malformed_header_rejected() -> None:
    body = '{"type": "purchase.created"}'
    with pytest.raises(SolvaPayError, match="malformed"):
        verify_webhook(body=body, signature="t=123", secret=SECRET)
