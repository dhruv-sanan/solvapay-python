"""Tests for idempotency key propagation and payload-hash helper."""

from __future__ import annotations

from unittest.mock import patch

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


def test_from_payload_no_bucket_is_pure_payload_hash() -> None:
    # time_bucket=None → same key regardless of when called
    key_a = from_payload("cus_1", "prd_x", time_bucket=None)
    key_b = from_payload("cus_1", "prd_x", time_bucket=None)
    assert key_a == key_b
    assert len(key_a) == 32
    # Different from day-bucket at any given time (bucket part changes hash)
    # (probabilistically true; same only if today's date happens to hash identically)
    key_day = from_payload("cus_1", "prd_x", time_bucket="day")
    assert key_a != key_day


def test_from_payload_day_bucket_changes_at_utc_midnight() -> None:
    import datetime

    day1 = datetime.datetime(2026, 5, 22, 23, 59, 59, tzinfo=datetime.timezone.utc)
    day2 = datetime.datetime(2026, 5, 23, 0, 0, 1, tzinfo=datetime.timezone.utc)

    with patch("solvapay.idempotency.datetime") as mock_dt:
        mock_dt.datetime.now.return_value = day1
        mock_dt.timezone = datetime.timezone
        key_before = from_payload("cus_1", "prd_x", time_bucket="day")

    with patch("solvapay.idempotency.datetime") as mock_dt:
        mock_dt.datetime.now.return_value = day2
        mock_dt.timezone = datetime.timezone
        key_after = from_payload("cus_1", "prd_x", time_bucket="day")

    assert key_before != key_after
