"""Tests for admin endpoints: products, plans, merchant, platform-config."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from solvapay import AsyncSolvaPay, Merchant, Plan, PlatformConfig, Product, SolvaPay

BASE = "https://api.solvapay.test"

_PRODUCT = {"reference": "prd_abc", "name": "Pro", "type": "recurring", "status": "active"}
_PLAN = {
    "reference": "pln_abc",
    "name": "Monthly",
    "type": "recurring",
    "price": 9.99,
    "currency": "USD",
}
_MERCHANT = {"merchantRef": "mrc_abc", "name": "Acme", "email": "acme@example.com"}
_PLATFORM_CONFIG = {"currency": "USD"}


# ---------------------------------------------------------------------------
# Sync tests
# ---------------------------------------------------------------------------


@respx.mock
def test_list_products(client: SolvaPay) -> None:
    route = respx.get(f"{BASE}/v1/sdk/products").mock(
        return_value=httpx.Response(200, json=[_PRODUCT])
    )
    products = client.list_products()
    assert route.called
    assert len(products) == 1
    assert isinstance(products[0], Product)
    assert products[0].reference == "prd_abc"


@respx.mock
def test_get_product(client: SolvaPay) -> None:
    route = respx.get(f"{BASE}/v1/sdk/products/prd_abc").mock(
        return_value=httpx.Response(200, json=_PRODUCT)
    )
    product = client.get_product("prd_abc")
    assert route.called
    assert product.name == "Pro"


@respx.mock
def test_create_product_sends_camelcase(client: SolvaPay) -> None:
    route = respx.post(f"{BASE}/v1/sdk/products").mock(
        return_value=httpx.Response(200, json=_PRODUCT)
    )
    product = client.create_product(name="Pro", type="recurring", default_currency="USD")
    assert route.called
    body = json.loads(route.calls.last.request.content)
    assert "defaultCurrency" in body
    assert "default_currency" not in body
    assert body["defaultCurrency"] == "USD"
    assert isinstance(product, Product)


@respx.mock
def test_delete_product(client: SolvaPay) -> None:
    route = respx.delete(f"{BASE}/v1/sdk/products/prd_abc").mock(
        return_value=httpx.Response(200, json={})
    )
    result = client.delete_product("prd_abc")
    assert route.called
    assert isinstance(result, dict)


@respx.mock
def test_clone_product(client: SolvaPay) -> None:
    route = respx.post(f"{BASE}/v1/sdk/products/prd_abc/clone").mock(
        return_value=httpx.Response(200, json={**_PRODUCT, "name": "Pro Copy"})
    )
    product = client.clone_product("prd_abc", new_name="Pro Copy")
    assert route.called
    body = json.loads(route.calls.last.request.content)
    assert body["newName"] == "Pro Copy"
    assert product.name == "Pro Copy"


@respx.mock
def test_list_plans(client: SolvaPay) -> None:
    route = respx.get(f"{BASE}/v1/sdk/products/prd_abc/plans").mock(
        return_value=httpx.Response(200, json=[_PLAN])
    )
    plans = client.list_plans("prd_abc")
    assert route.called
    assert len(plans) == 1
    assert isinstance(plans[0], Plan)
    assert plans[0].reference == "pln_abc"


@respx.mock
def test_create_plan(client: SolvaPay) -> None:
    route = respx.post(f"{BASE}/v1/sdk/products/prd_abc/plans").mock(
        return_value=httpx.Response(200, json=_PLAN)
    )
    plan = client.create_plan("prd_abc", name="Monthly", type="recurring", price=9.99)
    assert route.called
    assert isinstance(plan, Plan)
    assert plan.price == 9.99


@respx.mock
def test_update_plan(client: SolvaPay) -> None:
    route = respx.put(f"{BASE}/v1/sdk/products/prd_abc/plans/pln_abc").mock(
        return_value=httpx.Response(200, json={**_PLAN, "price": 14.99})
    )
    plan = client.update_plan("prd_abc", "pln_abc", price=14.99)
    assert route.called
    assert plan.price == 14.99


@respx.mock
def test_delete_plan(client: SolvaPay) -> None:
    route = respx.delete(f"{BASE}/v1/sdk/products/prd_abc/plans/pln_abc").mock(
        return_value=httpx.Response(200, json={})
    )
    result = client.delete_plan("prd_abc", "pln_abc")
    assert route.called
    assert isinstance(result, dict)


@respx.mock
def test_get_merchant(client: SolvaPay) -> None:
    route = respx.get(f"{BASE}/v1/sdk/merchant").mock(
        return_value=httpx.Response(200, json=_MERCHANT)
    )
    merchant = client.get_merchant()
    assert route.called
    assert isinstance(merchant, Merchant)
    assert merchant.merchant_ref == "mrc_abc"
    assert merchant.name == "Acme"


@respx.mock
def test_get_platform_config(client: SolvaPay) -> None:
    route = respx.get(f"{BASE}/v1/sdk/platform-config").mock(
        return_value=httpx.Response(200, json=_PLATFORM_CONFIG)
    )
    config = client.get_platform_config()
    assert route.called
    assert isinstance(config, PlatformConfig)
    assert config.currency == "USD"


# ---------------------------------------------------------------------------
# Async tests
# ---------------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_async_list_products(async_client: AsyncSolvaPay) -> None:
    route = respx.get(f"{BASE}/v1/sdk/products").mock(
        return_value=httpx.Response(200, json=[_PRODUCT])
    )
    products = await async_client.list_products()
    assert route.called
    assert isinstance(products[0], Product)


@respx.mock
@pytest.mark.asyncio
async def test_async_get_product(async_client: AsyncSolvaPay) -> None:
    route = respx.get(f"{BASE}/v1/sdk/products/prd_abc").mock(
        return_value=httpx.Response(200, json=_PRODUCT)
    )
    product = await async_client.get_product("prd_abc")
    assert route.called
    assert product.reference == "prd_abc"


@respx.mock
@pytest.mark.asyncio
async def test_async_create_product(async_client: AsyncSolvaPay) -> None:
    route = respx.post(f"{BASE}/v1/sdk/products").mock(
        return_value=httpx.Response(200, json=_PRODUCT)
    )
    product = await async_client.create_product(
        name="Pro", type="recurring", default_currency="USD"
    )
    assert route.called
    body = json.loads(route.calls.last.request.content)
    assert body["defaultCurrency"] == "USD"
    assert isinstance(product, Product)


@respx.mock
@pytest.mark.asyncio
async def test_async_delete_product(async_client: AsyncSolvaPay) -> None:
    route = respx.delete(f"{BASE}/v1/sdk/products/prd_abc").mock(
        return_value=httpx.Response(200, json={})
    )
    await async_client.delete_product("prd_abc")
    assert route.called


@respx.mock
@pytest.mark.asyncio
async def test_async_clone_product(async_client: AsyncSolvaPay) -> None:
    route = respx.post(f"{BASE}/v1/sdk/products/prd_abc/clone").mock(
        return_value=httpx.Response(200, json={**_PRODUCT, "name": "Pro Copy"})
    )
    product = await async_client.clone_product("prd_abc", new_name="Pro Copy")
    assert route.called
    assert product.name == "Pro Copy"


@respx.mock
@pytest.mark.asyncio
async def test_async_list_plans(async_client: AsyncSolvaPay) -> None:
    route = respx.get(f"{BASE}/v1/sdk/products/prd_abc/plans").mock(
        return_value=httpx.Response(200, json=[_PLAN])
    )
    plans = await async_client.list_plans("prd_abc")
    assert route.called
    assert isinstance(plans[0], Plan)


@respx.mock
@pytest.mark.asyncio
async def test_async_create_plan(async_client: AsyncSolvaPay) -> None:
    route = respx.post(f"{BASE}/v1/sdk/products/prd_abc/plans").mock(
        return_value=httpx.Response(200, json=_PLAN)
    )
    plan = await async_client.create_plan("prd_abc", name="Monthly", type="recurring")
    assert route.called
    assert isinstance(plan, Plan)


@respx.mock
@pytest.mark.asyncio
async def test_async_update_plan(async_client: AsyncSolvaPay) -> None:
    route = respx.put(f"{BASE}/v1/sdk/products/prd_abc/plans/pln_abc").mock(
        return_value=httpx.Response(200, json={**_PLAN, "price": 14.99})
    )
    plan = await async_client.update_plan("prd_abc", "pln_abc", price=14.99)
    assert route.called
    assert plan.price == 14.99


@respx.mock
@pytest.mark.asyncio
async def test_async_delete_plan(async_client: AsyncSolvaPay) -> None:
    route = respx.delete(f"{BASE}/v1/sdk/products/prd_abc/plans/pln_abc").mock(
        return_value=httpx.Response(200, json={})
    )
    await async_client.delete_plan("prd_abc", "pln_abc")
    assert route.called


@respx.mock
@pytest.mark.asyncio
async def test_async_get_merchant(async_client: AsyncSolvaPay) -> None:
    route = respx.get(f"{BASE}/v1/sdk/merchant").mock(
        return_value=httpx.Response(200, json=_MERCHANT)
    )
    merchant = await async_client.get_merchant()
    assert route.called
    assert isinstance(merchant, Merchant)


@respx.mock
@pytest.mark.asyncio
async def test_async_get_platform_config(async_client: AsyncSolvaPay) -> None:
    route = respx.get(f"{BASE}/v1/sdk/platform-config").mock(
        return_value=httpx.Response(200, json=_PLATFORM_CONFIG)
    )
    config = await async_client.get_platform_config()
    assert route.called
    assert isinstance(config, PlatformConfig)
