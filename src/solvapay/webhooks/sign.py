"""Webhook signing helper for tests and outbound webhook sending."""

from __future__ import annotations

import hashlib
import hmac
import time as _time


def sign_webhook(
    body: bytes,
    secret: str,
    *,
    timestamp: int | None = None,
) -> str:
    """Produce a ``sv-signature`` header value for a webhook payload.

    Returns a string in the format ``t={ts},v1={hmac}`` — the same format
    verified by :func:`solvapay.webhooks.verify.verify_webhook` and
    :class:`solvapay.webhooks.pipeline.WebhookPipeline`.

    Args:
        body: Raw request body bytes.
        secret: Webhook secret (``whsec_...``).
        timestamp: Unix timestamp. Defaults to current time.

    Example::

        from solvapay.webhooks import sign_webhook, verify_webhook

        sig = sign_webhook(b'{"id":"evt_1"}', secret="whsec_test")
        verify_webhook(b'{"id":"evt_1"}', sig, secret="whsec_test")  # passes
    """
    ts = timestamp if timestamp is not None else int(_time.time())
    payload = f"{ts}.{body.decode('utf-8')}"
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"
