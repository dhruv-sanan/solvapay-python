"""Tests for lifecycle ops: track_usage, update_customer, get_customer_balance,
cancel_purchase, reactivate_purchase — sync and async."""

from __future__ import annotations

import httpx
import pytest
import respx

from solvapay import AsyncSolvaPay, SolvaPay

BASE = "https://api.solvapay.test"


@pytest.fixture
def client() -> SolvaPay:
    return SolvaPay(api_key="sk_test_dummy", base_url=BASE)


@pytest.fixture
def async_client() -> AsyncSolvaPay:
    return AsyncSolvaPay(api_key="sk_test_dummy", base_url=BASE)


# ---------------------------------------------------------------------------
# track_usage
# ---------------------------------------------------------------------------


@respx.mock
def test_track_usage_sends_correct_body(client: SolvaPay) -> None:
    route = respx.post(f"{BASE}/v1/sdk/usages").mock(
        return_value=httpx.Response(200, json={"recorded": True})
    )
    result = client.track_usage(
        customer_ref="cus_1", product_ref="prd_A", meter_name="api_calls", units=5.0
    )
    assert route.called
    import json

    body = json.loads(route.calls[0].request.content)
    assert body == {
        "customerRef": "cus_1",
        "productRef": "prd_A",
        "meterName": "api_calls",
        "units": 5.0,
    }
    assert result == {"recorded": True}


@respx.mock
async def test_async_track_usage_sends_correct_body(async_client: AsyncSolvaPay) -> None:
    route = respx.post(f"{BASE}/v1/sdk/usages").mock(
        return_value=httpx.Response(200, json={"recorded": True})
    )
    result = await async_client.track_usage(
        customer_ref="cus_1", product_ref="prd_A", meter_name="api_calls", units=3.0
    )
    assert route.called
    assert result == {"recorded": True}


# ---------------------------------------------------------------------------
# update_customer
# ---------------------------------------------------------------------------


@respx.mock
def test_update_customer_sends_patch(client: SolvaPay) -> None:
    route = respx.patch(f"{BASE}/v1/sdk/customers/cus_1").mock(
        return_value=httpx.Response(200, json={"customerRef": "cus_1", "email": "new@example.com"})
    )
    customer = client.update_customer("cus_1", email="new@example.com")
    assert route.called
    assert customer.customer_ref == "cus_1"
    assert customer.email == "new@example.com"


@respx.mock
async def test_async_update_customer_sends_patch(async_client: AsyncSolvaPay) -> None:
    route = respx.patch(f"{BASE}/v1/sdk/customers/cus_1").mock(
        return_value=httpx.Response(200, json={"customerRef": "cus_1", "name": "Alice"})
    )
    customer = await async_client.update_customer("cus_1", name="Alice")
    assert route.called
    assert customer.name == "Alice"


# ---------------------------------------------------------------------------
# get_customer_balance
# ---------------------------------------------------------------------------


@respx.mock
def test_get_customer_balance_returns_balance(client: SolvaPay) -> None:
    respx.get(f"{BASE}/v1/sdk/customers/cus_1/balance").mock(
        return_value=httpx.Response(
            200,
            json={
                "customerRef": "cus_1",
                "credits": 4250,
                "displayCurrency": "USD",
                "creditsPerMinorUnit": 100,
                "displayExchangeRate": 1.0,
            },
        )
    )
    balance = client.get_customer_balance("cus_1")
    assert balance.customer_ref == "cus_1"
    assert balance.credits == 4250
    assert balance.credits_per_minor_unit == 100
    assert (
        balance.balance == 0.425
    )  # derived: credits / credits_per_minor_unit / 100 (minor→major unit)
    assert balance.currency == "USD"


@respx.mock
async def test_async_get_customer_balance_returns_balance(async_client: AsyncSolvaPay) -> None:
    respx.get(f"{BASE}/v1/sdk/customers/cus_1/balance").mock(
        return_value=httpx.Response(
            200,
            json={
                "customerRef": "cus_1",
                "credits": 1000,
                "displayCurrency": "EUR",
                "creditsPerMinorUnit": 100,
                "displayExchangeRate": 1.0,
            },
        )
    )
    balance = await async_client.get_customer_balance("cus_1")
    assert balance.balance == 0.10
    assert balance.currency == "EUR"


# ---------------------------------------------------------------------------
# cancel_purchase
# ---------------------------------------------------------------------------


@respx.mock
def test_cancel_purchase_posts_with_reason(client: SolvaPay) -> None:
    route = respx.post(f"{BASE}/v1/sdk/purchases/pur_1/cancel").mock(
        return_value=httpx.Response(200, json={"cancelled": True})
    )
    result = client.cancel_purchase("pur_1", reason="user request")
    assert route.called
    import json

    body = json.loads(route.calls[0].request.content)
    assert body.get("reason") == "user request"
    assert result == {"cancelled": True}


@respx.mock
async def test_async_cancel_purchase(async_client: AsyncSolvaPay) -> None:
    route = respx.post(f"{BASE}/v1/sdk/purchases/pur_1/cancel").mock(
        return_value=httpx.Response(200, json={"cancelled": True})
    )
    result = await async_client.cancel_purchase("pur_1")
    assert route.called
    assert result == {"cancelled": True}


# ---------------------------------------------------------------------------
# reactivate_purchase
# ---------------------------------------------------------------------------


@respx.mock
def test_reactivate_purchase_posts_to_correct_path(client: SolvaPay) -> None:
    route = respx.post(f"{BASE}/v1/sdk/purchases/pur_1/reactivate").mock(
        return_value=httpx.Response(200, json={"reactivated": True})
    )
    result = client.reactivate_purchase("pur_1")
    assert route.called
    assert result == {"reactivated": True}


@respx.mock
async def test_async_reactivate_purchase(async_client: AsyncSolvaPay) -> None:
    route = respx.post(f"{BASE}/v1/sdk/purchases/pur_1/reactivate").mock(
        return_value=httpx.Response(200, json={"reactivated": True})
    )
    result = await async_client.reactivate_purchase("pur_1")
    assert route.called
    assert result == {"reactivated": True}
