"""Webhook secret rotation (HLD V1.7). Full impl in v0.9; v0.8 ships interface + single-secret fallback."""

from __future__ import annotations

import hashlib
import hmac
from collections.abc import Sequence


class MultiSecretVerifier:
    """Try primary secret; fall back to secondary on HMAC mismatch (not age failure).

    Both comparisons are constant-time (hmac.compare_digest).
    v0.8: single-secret fallback only; full rotation ships in v0.9.
    """

    def __init__(self, secrets: Sequence[str]) -> None:
        if not secrets:
            raise ValueError("MultiSecretVerifier requires at least one secret")
        self._secrets = list(secrets)

    def verify(self, *, payload: str, received: str) -> bool:
        """Return True if ANY secret produces a matching HMAC."""
        for secret in self._secrets:
            expected = hmac.new(
                secret.encode(),
                payload.encode(),
                hashlib.sha256,
            ).hexdigest()
            if hmac.compare_digest(expected, received):
                return True
        return False
