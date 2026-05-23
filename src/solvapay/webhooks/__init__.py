"""SolvaPay webhooks package.

Backward-compat re-export (v0.7 callers unaffected):
    verify_webhook — HMAC signature verification

New in v0.8:
    WebhookPipeline        — full verify + dedup pipeline (HLD V1.7)
    WebhookEnvelope        — typed event envelope
    InMemorySeenEventCache — sync dedup cache
    SeenEventCache         — Protocol for custom caches
    MultiSecretVerifier    — secret rotation verifier

New in v0.9:
    AsyncSeenEventCache         — async Protocol for custom caches
    AsyncInMemorySeenEventCache — async in-memory dedup cache
    sign_webhook                — produce sv-signature header for testing/sending
"""

from __future__ import annotations

from solvapay.webhooks.envelope import WebhookEnvelope
from solvapay.webhooks.pipeline import WebhookPipeline
from solvapay.webhooks.replay import (
    AsyncInMemorySeenEventCache,
    AsyncSeenEventCache,
    InMemorySeenEventCache,
    SeenEventCache,
)
from solvapay.webhooks.rotation import MultiSecretVerifier
from solvapay.webhooks.sign import sign_webhook
from solvapay.webhooks.verify import verify_webhook

__all__ = [
    "AsyncInMemorySeenEventCache",
    "AsyncSeenEventCache",
    "InMemorySeenEventCache",
    "MultiSecretVerifier",
    "SeenEventCache",
    "WebhookEnvelope",
    "WebhookPipeline",
    "sign_webhook",
    "verify_webhook",
]
