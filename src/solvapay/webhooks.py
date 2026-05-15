"""Webhook signature verification.

Mirrors @solvapay/server verifyWebhook. HMAC-SHA256 over "{timestamp}.{body}"
with header format "t={ts},v1={hmac}". 5-minute tolerance. Constant-time compare.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any, TypeVar

from solvapay.exceptions import SolvaPayError

T = TypeVar("T")


def _parse_signature_header(signature: str) -> tuple[int, str]:
    parts: dict[str, str] = {}
    for chunk in signature.split(","):
        if "=" in chunk:
            k, _, v = chunk.partition("=")
            parts[k.strip()] = v.strip()
    if "t" not in parts or "v1" not in parts:
        raise SolvaPayError("Webhook signature header malformed (missing t= or v1=)")
    try:
        ts = int(parts["t"])
    except ValueError as exc:
        raise SolvaPayError("Webhook signature timestamp not an integer") from exc
    return ts, parts["v1"]


def verify_webhook(
    *,
    body: str,
    signature: str,
    secret: str,
    tolerance: int = 300,
    parse_as: type[T] | None = None,
) -> dict[str, Any] | T:
    """Verify a SolvaPay webhook signature and return the parsed event.

    Args:
        body: Raw request body string. Must be the exact bytes signed by
              SolvaPay — do not reformat JSON or strip whitespace.
        signature: Value of the sv-signature request header.
        secret: Webhook signing secret (starts with whsec_).
        tolerance: Max seconds since signature timestamp. Default 300 (5 min).
        parse_as: Optional pydantic type to validate the event into. Pass
                  `WebhookEvent` for a typed discriminated union. Omit for
                  backwards-compatible dict return.

    Returns:
        Parsed webhook event as dict (default) or instance of `parse_as`.

    Raises:
        SolvaPayError: Header malformed, timestamp too old, signature mismatch,
                       or body not valid JSON.
    """
    timestamp, received = _parse_signature_header(signature)

    age = abs(int(time.time()) - timestamp)
    if age > tolerance:
        raise SolvaPayError(f"Webhook signature timestamp too old (age={age}s)")

    expected = hmac.new(
        secret.encode(),
        f"{timestamp}.{body}".encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, received):
        raise SolvaPayError("Webhook signature mismatch")

    try:
        event: dict[str, Any] = json.loads(body)
    except json.JSONDecodeError as exc:
        raise SolvaPayError("Webhook body is not valid JSON") from exc

    if parse_as is None:
        return event
    from pydantic import TypeAdapter

    return TypeAdapter(parse_as).validate_python(event)
