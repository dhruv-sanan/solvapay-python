"""Webhook secret rotation (HLD V1.7)."""

from __future__ import annotations

import hashlib
import hmac
from collections.abc import Sequence


class MultiSecretVerifier:
    """Try primary secret; fall back to secondary on HMAC mismatch (not age failure).

    Both comparisons are constant-time (hmac.compare_digest). Age check happens
    upstream in WebhookPipeline.process — this class only handles HMAC matching.
    Pass secrets in order of preference: primary first, rotation candidates after.
    """

    def __init__(self, secrets: Sequence[str]) -> None:
        if not secrets:
            raise ValueError("MultiSecretVerifier requires at least one secret")
        self._secrets = list(secrets)

    def verify(self, *, payload: str, received: str) -> bool:
        """Return True if the primary secret matches, or any fallback secret matches.

        Short-circuits on first match. Each comparison is constant-time.
        """
        for secret in self._secrets:
            expected = hmac.new(
                secret.encode(),
                payload.encode(),
                hashlib.sha256,
            ).hexdigest()
            if hmac.compare_digest(expected, received):
                return True
        return False
