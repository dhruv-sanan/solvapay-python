"""Idempotency key helpers for SolvaPay SDK."""

from __future__ import annotations

import hashlib
import json


def from_payload(*parts: str | int | float | None) -> str:
    """SHA256 of stable-serialized payload parts → 32-hex-char key.

    Deterministic, 24h-safe. Caller is responsible for input stability.
    Retried POSTs must supply the *same* key as the original call.
    """
    data = json.dumps(parts, separators=(",", ":"), default=str)
    return hashlib.sha256(data.encode()).hexdigest()[:32]
