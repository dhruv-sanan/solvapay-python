"""Tests for sign_webhook helper — round-trip with verify_webhook."""

from __future__ import annotations

from solvapay.webhooks.sign import sign_webhook
from solvapay.webhooks.verify import verify_webhook


def test_sign_webhook_round_trip() -> None:
    body = b'{"id":"evt_1","type":"payment.succeeded"}'
    secret = "whsec_test_secret"
    sig = sign_webhook(body, secret)
    result = verify_webhook(body=body.decode(), signature=sig, secret=secret, tolerance=300)
    assert result["id"] == "evt_1"


def test_sign_webhook_header_format() -> None:
    sig = sign_webhook(b"{}", "whsec_x", timestamp=1234567890)
    assert sig.startswith("t=1234567890,v1=")
    _, v1_part = sig.split(",", 1)
    assert v1_part.startswith("v1=")
    hmac_value = v1_part[3:]
    assert len(hmac_value) == 64  # SHA-256 hex digest


def test_sign_webhook_explicit_timestamp() -> None:
    body = b'{"id":"evt_fixed"}'
    sig1 = sign_webhook(body, "secret", timestamp=1000000000)
    sig2 = sign_webhook(body, "secret", timestamp=1000000000)
    assert sig1 == sig2


def test_sign_webhook_different_secrets_differ() -> None:
    body = b'{"id":"evt_1"}'
    sig_a = sign_webhook(body, "secret_a", timestamp=100)
    sig_b = sign_webhook(body, "secret_b", timestamp=100)
    assert sig_a != sig_b
