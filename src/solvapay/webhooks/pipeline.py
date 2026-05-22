"""WebhookPipeline — verify + deduplicate in one call (HLD V1.7 WP2)."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from collections.abc import Sequence
from typing import Any, Callable

from solvapay.exceptions import SolvaPayError
from solvapay.webhooks.envelope import WebhookEnvelope
from solvapay.webhooks.replay import InMemorySeenEventCache, SeenEventCache
from solvapay.webhooks.verify import _parse_signature_header


class WebhookPipeline:
    """Verify signature, check clock skew, deduplicate (HLD V1.7 WP2).

    TWO separate knobs (HLD WP2 lock):
        max_clock_skew_seconds  — clock tolerance (default 300s)
        replay_ttl_seconds      — replay-attack dedup window (default 600s)
    """

    def __init__(
        self,
        secrets: Sequence[str],
        *,
        max_clock_skew_seconds: int = 300,
        replay_ttl_seconds: int = 600,
        seen_cache: SeenEventCache | None = None,
        dispatcher: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        if not secrets:
            raise ValueError("WebhookPipeline requires at least one secret")
        self._secrets = list(secrets)
        self._max_clock_skew_seconds = max_clock_skew_seconds
        self._replay_ttl_seconds = replay_ttl_seconds
        self._cache: SeenEventCache = seen_cache or InMemorySeenEventCache()
        self._dispatcher = dispatcher

    def process(self, body: bytes, signature: str) -> WebhookEnvelope:
        """Verify signature, check age, deduplicate, return envelope.

        Raises SolvaPayError on any verification failure.
        """
        body_str = body.decode("utf-8") if isinstance(body, bytes) else body
        timestamp, received = _parse_signature_header(signature)

        age = abs(int(time.time()) - timestamp)
        if age > self._max_clock_skew_seconds:
            raise SolvaPayError(
                f"Webhook clock skew too large (age={age}s, max={self._max_clock_skew_seconds}s)"
            )

        payload = f"{timestamp}.{body_str}"
        verified = False
        for secret in self._secrets:
            expected = hmac.new(
                secret.encode(),
                payload.encode(),
                hashlib.sha256,
            ).hexdigest()
            if hmac.compare_digest(expected, received):
                verified = True
                break
        if not verified:
            raise SolvaPayError("Webhook signature mismatch")

        try:
            event: dict[str, Any] = json.loads(body_str)
        except json.JSONDecodeError as exc:
            raise SolvaPayError("Webhook body is not valid JSON") from exc

        event_id: str = str(event.get("id", f"{timestamp}-{received[:8]}"))
        if not self._cache.try_claim(event_id, self._replay_ttl_seconds):
            raise SolvaPayError(f"Webhook event already processed (id={event_id!r})")

        envelope = WebhookEnvelope(
            event_id=event_id,
            timestamp=timestamp,
            body=body if isinstance(body, bytes) else body.encode("utf-8"),
            event=event,
        )
        if self._dispatcher is not None:
            self._dispatcher(event)
        return envelope
