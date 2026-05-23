"""Tests for ASGI webhook adapter."""

from __future__ import annotations

import json

import httpx
import pytest

from solvapay.adapters.asgi import webhook_app
from solvapay.webhooks import WebhookEnvelope, WebhookPipeline
from solvapay.webhooks.sign import sign_webhook

SECRET = "whsec_test_asgi"
BODY = json.dumps({"id": "evt_asgi_1", "type": "payment.succeeded"}).encode()


def _make_pipeline() -> WebhookPipeline:
    return WebhookPipeline(secrets=[SECRET], max_clock_skew_seconds=300)


@pytest.mark.anyio
async def test_valid_webhook_calls_on_event() -> None:
    received: list[WebhookEnvelope] = []

    async def on_event(envelope: WebhookEnvelope) -> None:
        received.append(envelope)

    app = webhook_app(_make_pipeline(), on_event)
    sig = sign_webhook(BODY, SECRET)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/webhook", content=BODY, headers={"sv-signature": sig})

    assert resp.status_code == 200
    assert len(received) == 1
    assert received[0].event["id"] == "evt_asgi_1"


@pytest.mark.anyio
async def test_bad_signature_returns_400() -> None:
    app = webhook_app(_make_pipeline(), lambda e: None)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/webhook", content=BODY, headers={"sv-signature": "t=1,v1=badhash"}
        )

    assert resp.status_code == 400


@pytest.mark.anyio
async def test_missing_signature_header_returns_400() -> None:
    app = webhook_app(_make_pipeline(), lambda e: None)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/webhook", content=BODY)

    assert resp.status_code == 400


@pytest.mark.anyio
async def test_wrong_path_returns_404() -> None:
    app = webhook_app(_make_pipeline(), lambda e: None, path="/webhook")
    sig = sign_webhook(BODY, SECRET)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post("/other", content=BODY, headers={"sv-signature": sig})

    assert resp.status_code == 404


@pytest.mark.anyio
async def test_non_post_returns_405() -> None:
    app = webhook_app(_make_pipeline(), lambda e: None)
    sig = sign_webhook(BODY, SECRET)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/webhook", headers={"sv-signature": sig})

    assert resp.status_code == 405
