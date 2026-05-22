"""SolvaPay webhooks package.

Backward-compat re-export (v0.7 callers unaffected):
    verify_webhook — HMAC signature verification

New in v0.8:
    WebhookPipeline     — full verify + dedup pipeline (HLD V1.7)
    WebhookEnvelope     — typed event envelope
    InMemorySeenEventCache — sync dedup cache
    SeenEventCache      — Protocol for custom caches
"""

from __future__ import annotations

from solvapay.webhooks.envelope import WebhookEnvelope
from solvapay.webhooks.pipeline import WebhookPipeline
from solvapay.webhooks.replay import InMemorySeenEventCache, SeenEventCache
from solvapay.webhooks.rotation import MultiSecretVerifier
from solvapay.webhooks.verify import verify_webhook

__all__ = [
    "InMemorySeenEventCache",
    "MultiSecretVerifier",
    "SeenEventCache",
    "WebhookEnvelope",
    "WebhookPipeline",
    "verify_webhook",
]
