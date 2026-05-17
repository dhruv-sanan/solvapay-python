"""Tests for idempotency key propagation and payload-hash helper."""

from __future__ import annotations

import httpx
import respx

from solvapay import AsyncSolvaPay, SolvaPay
from solvapay.idempotency import from_payload

BASE = "https://api.solvapay.test"
SESSION_RESPONSE = {"sessionId": "sess_x", "checkoutUrl": "https://checkout.solvapay.com/sess_x"}


@respx.mock
def test_idempotency_key_sent_as_header_on_create_checkout_session(client: SolvaPay) -> None:
    route = respx.post(f"{BASE}/v1/sdk/checkout-sessions").mock(
        return_value=httpx.Response(200, json=SESSION_RESPONSE)
    )
    client.create_checkout_session(
        customer_ref="cus_123",
        product_ref="prd_abc",
        idempotency_key="idem_test_key",
    )
    assert route.calls.last.request.headers["Idempotency-Key"] == "idem_test_key"


@respx.mock
def test_idempotency_key_omitted_when_none(client: SolvaPay) -> None:
    route = respx.post(f"{BASE}/v1/sdk/checkout-sessions").mock(
        return_value=httpx.Response(200, json=SESSION_RESPONSE)
    )
    client.create_checkout_session(customer_ref="cus_123", product_ref="prd_abc")
    assert "Idempotency-Key" not in route.calls.last.request.headers


def test_from_payload_deterministic() -> None:
    key1 = from_payload("cus_123", "prd_abc", 42)
    key2 = from_payload("cus_123", "prd_abc", 42)
    assert key1 == key2
    assert len(key1) == 32


def test_from_payload_different_inputs_differ() -> None:
    assert from_payload("cus_123", "prd_abc") != from_payload("cus_123", "prd_xyz")
    assert from_payload("a") != from_payload("b")
    assert from_payload("cus_123", None) != from_payload("cus_123", "prd_abc")


@respx.mock
async def test_async_create_checkout_session_sends_idempotency_key(
    async_client: AsyncSolvaPay,
) -> None:
    route = respx.post(f"{BASE}/v1/sdk/checkout-sessions").mock(
        return_value=httpx.Response(200, json=SESSION_RESPONSE)
    )
    await async_client.create_checkout_session(
        customer_ref="cus_123",
        product_ref="prd_abc",
        idempotency_key="async_idem_key",
    )
    assert route.calls.last.request.headers["Idempotency-Key"] == "async_idem_key"
