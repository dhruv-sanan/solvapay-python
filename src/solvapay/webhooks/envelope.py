"""WebhookEnvelope — parsed webhook event with metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class WebhookEnvelope:
    """Parsed and verified webhook event (HLD V1.7)."""

    event_id: str
    timestamp: int
    body: bytes
    event: dict[str, Any]
