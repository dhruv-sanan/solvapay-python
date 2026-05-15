"""Tests for AsyncSolvaPay and paywall.require_async."""
from __future__ import annotations

import httpx
import pytest
import respx

from solvapay import AsyncSolvaPay, paywall
from solvapay.paywall import PaywallRequired


@pytest.fixture
def async_client() -> AsyncSolvaPay:
    return AsyncSolvaPay(api_key="sk_test_dummy", base_url="https://api.solvapay.test")


# ---------------------------------------------------------------------------
# create_checkout_session
# ---------------------------------------------------------------------------


@respx.mock
async def test_async_create_checkout_session_sends_correct_request(
    async_client: AsyncSolvaPay,
) -> None:
    route = respx.post("https://api.solvapay.test/v1/sdk/checkout-sessions").mock(
        return_value=httpx.Response(
            200, json={"sessionId": "sess_abc", "checkoutUrl": "https://pay.example.com/sess_abc"}
        )
    )
    session = await async_client.create_checkout_session(
        customer_ref="cus_1", product_ref="prd_A", plan_ref="plan_B", return_url="https://ret.example"
    )
    assert route.called
    assert session.session_id == "sess_abc"
    assert session.checkout_url == "https://pay.example.com/sess_abc"


@respx.mock
async def test_async_create_checkout_session_omits_optional_fields(
    async_client: AsyncSolvaPay,
) -> None:
    route = respx.post("https://api.solvapay.test/v1/sdk/checkout-sessions").mock(
        return_value=httpx.Response(
            200, json={"sessionId": "sess_min", "checkoutUrl": "https://pay.example.com/sess_min"}
        )
    )
    await async_client.create_checkout_session(customer_ref="cus_1", product_ref="prd_A")
    sent = route.calls[0].request
    import json
    body = json.loads(sent.content)
    assert "planRef" not in body
    assert "returnUrl" not in body


# ---------------------------------------------------------------------------
# ensure_customer
# ---------------------------------------------------------------------------


@respx.mock
async def test_async_ensure_customer_returns_existing(async_client: AsyncSolvaPay) -> None:
    respx.get("https://api.solvapay.test/v1/sdk/customers").mock(
        return_value=httpx.Response(200, json={"customerRef": "cus_existing"})
    )
    ref = await async_client.ensure_customer("cus_existing")
    assert ref == "cus_existing"


@respx.mock
async def test_async_ensure_customer_creates_on_404(async_client: AsyncSolvaPay) -> None:
    respx.get("https://api.solvapay.test/v1/sdk/customers").mock(
        return_value=httpx.Response(404, json={"error": "not found"})
    )
    respx.post("https://api.solvapay.test/v1/sdk/customers").mock(
        return_value=httpx.Response(200, json={"customerRef": "cus_new"})
    )
    ref = await async_client.ensure_customer("cus_new", email="new@example.com")
    assert ref == "cus_new"


# ---------------------------------------------------------------------------
# get_customer
# ---------------------------------------------------------------------------


@respx.mock
async def test_async_get_customer_by_ref(async_client: AsyncSolvaPay) -> None:
    respx.get("https://api.solvapay.test/v1/sdk/customers/cus_123").mock(
        return_value=httpx.Response(
            200, json={"customerRef": "cus_123", "email": "a@b.com"}
        )
    )
    customer = await async_client.get_customer("cus_123")
    assert customer.customer_ref == "cus_123"


@respx.mock
async def test_async_get_customer_by_external_ref(async_client: AsyncSolvaPay) -> None:
    respx.get("https://api.solvapay.test/v1/sdk/customers").mock(
        return_value=httpx.Response(
            200, json={"customerRef": "cus_456", "email": "b@b.com"}
        )
    )
    customer = await async_client.get_customer(external_ref="ext_456")
    assert customer.customer_ref == "cus_456"


# ---------------------------------------------------------------------------
# check_limits
# ---------------------------------------------------------------------------


@respx.mock
async def test_async_check_limits_within(async_client: AsyncSolvaPay) -> None:
    respx.post("https://api.solvapay.test/v1/sdk/limits").mock(
        return_value=httpx.Response(200, json={"withinLimits": True, "remaining": 10})
    )
    limits = await async_client.check_limits(customer_ref="cus_1", product_ref="prd_A")
    assert limits.within_limits is True
    assert limits.remaining == 10


@respx.mock
async def test_async_check_limits_exceeded(async_client: AsyncSolvaPay) -> None:
    respx.post("https://api.solvapay.test/v1/sdk/limits").mock(
        return_value=httpx.Response(
            200, json={"withinLimits": False, "remaining": 0, "checkoutUrl": "https://checkout.example"}
        )
    )
    limits = await async_client.check_limits(customer_ref="cus_1", product_ref="prd_A")
    assert limits.within_limits is False
    assert limits.checkout_url == "https://checkout.example"


# ---------------------------------------------------------------------------
# paywall.require_async
# ---------------------------------------------------------------------------


@respx.mock
async def test_require_async_passes_through_within_limits() -> None:
    respx.post("https://api.solvapay.test/v1/sdk/limits").mock(
        return_value=httpx.Response(200, json={"withinLimits": True, "remaining": 5})
    )
    sv = AsyncSolvaPay(api_key="sk_test_dummy", base_url="https://api.solvapay.test")

    @paywall.require_async(product="prd_A", client=sv)
    async def gated(*, customer_ref: str) -> str:
        return "result"

    result = await gated(customer_ref="cus_1")
    assert result == "result"


@respx.mock
async def test_require_async_raises_paywall_required_when_exceeded() -> None:
    respx.post("https://api.solvapay.test/v1/sdk/limits").mock(
        return_value=httpx.Response(
            200, json={"withinLimits": False, "remaining": 0, "checkoutUrl": "https://checkout.example"}
        )
    )
    sv = AsyncSolvaPay(api_key="sk_test_dummy", base_url="https://api.solvapay.test")

    @paywall.require_async(product="prd_A", client=sv)
    async def gated(*, customer_ref: str) -> str:
        return "result"

    with pytest.raises(PaywallRequired) as exc_info:
        await gated(customer_ref="cus_1")
    assert exc_info.value.checkout_url == "https://checkout.example"


# ---------------------------------------------------------------------------
# context manager
# ---------------------------------------------------------------------------


@respx.mock
async def test_async_context_manager() -> None:
    respx.post("https://api.solvapay.test/v1/sdk/checkout-sessions").mock(
        return_value=httpx.Response(
            200, json={"sessionId": "sess_ctx", "checkoutUrl": "https://pay.example.com/ctx"}
        )
    )
    async with AsyncSolvaPay(api_key="sk_test_dummy", base_url="https://api.solvapay.test") as sv:
        session = await sv.create_checkout_session(customer_ref="cus_1", product_ref="prd_A")
    assert session.session_id == "sess_ctx"
