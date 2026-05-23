"""Tests for MultiSecretVerifier secret rotation paths."""

from __future__ import annotations

from solvapay.webhooks.rotation import MultiSecretVerifier


def _make_payload(secret: str, payload: str) -> str:
    import hashlib
    import hmac

    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def test_primary_secret_matches() -> None:
    verifier = MultiSecretVerifier(["secret_primary", "secret_old"])
    payload = "1234567890.{}"
    received = _make_payload("secret_primary", payload)
    assert verifier.verify(payload=payload, received=received) is True


def test_primary_mismatch_secondary_matches() -> None:
    verifier = MultiSecretVerifier(["secret_old", "secret_new"])
    payload = "1234567890.{}"
    received = _make_payload("secret_new", payload)
    assert verifier.verify(payload=payload, received=received) is True


def test_all_secrets_mismatch_returns_false() -> None:
    verifier = MultiSecretVerifier(["bad_secret_a", "bad_secret_b"])
    payload = "1234567890.{}"
    received = _make_payload("correct_secret", payload)
    assert verifier.verify(payload=payload, received=received) is False


def test_single_secret_matches() -> None:
    verifier = MultiSecretVerifier(["only_secret"])
    payload = "9999999999.test_body"
    received = _make_payload("only_secret", payload)
    assert verifier.verify(payload=payload, received=received) is True


def test_empty_secrets_raises() -> None:
    import pytest

    with pytest.raises(ValueError, match="at least one secret"):
        MultiSecretVerifier([])
