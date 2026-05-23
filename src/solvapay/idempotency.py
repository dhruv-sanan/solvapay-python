"""Idempotency key helpers for SolvaPay SDK."""

from __future__ import annotations

import datetime
import hashlib
import json
from typing import Literal


def from_payload(
    *parts: str | int | float | None,
    time_bucket: Literal["day", "hour"] | None = "day",
) -> str:
    """SHA256 of stable-serialized payload parts → 32-hex-char key.

    Args:
        *parts: Stable payload fields that uniquely identify the request.
        time_bucket: Controls replay-ambiguity window.
            ``"day"``  (default) — appends current UTC date; key changes at midnight.
            ``"hour"`` — appends current UTC hour; key changes every hour.
            ``None``   — pure payload hash; deterministic across time (use only when
                         caller manages TTL externally).

    Retried POSTs MUST reuse the *same* key as the original call. A bucket
    roll (day/hour boundary) produces a different key, which the server treats
    as a new request — do not retry across a bucket boundary without intent.
    """
    bucket_part: str | None = None
    now = datetime.datetime.now(datetime.timezone.utc)
    if time_bucket == "day":
        bucket_part = now.strftime("%Y-%m-%d")
    elif time_bucket == "hour":
        bucket_part = now.strftime("%Y-%m-%dT%H")
    all_parts = (*parts, bucket_part) if bucket_part is not None else parts
    data = json.dumps(all_parts, separators=(",", ":"), default=str)
    return hashlib.sha256(data.encode()).hexdigest()[:32]
