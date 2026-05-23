"""Tests for api_version pinning (Solvapay-Version header) — HLD V1.13."""

from __future__ import annotations

import httpx
import respx

from solvapay import AsyncSolvaPay, SolvaPay

BASE = "https://api.solvapay.test"
_LIMITS_RESP = {"withinLimits": True, "remaining": 10, "meterName": "calls"}


@respx.mock
def test_api_version_header_sent() -> None:
    sv = SolvaPay(api_key="sk_test", base_url=BASE, api_version="2026-05-22")
    route = respx.post(f"{BASE}/v1/sdk/limits").mock(
        return_value=httpx.Response(200, json=_LIMITS_RESP)
    )
    sv.limits.check(customer_ref="cus_1", product_ref="prd_1")
    assert route.calls.last.request.headers["Solvapay-Version"] == "2026-05-22"


@respx.mock
def test_api_version_none_omits_header() -> None:
    sv = SolvaPay(api_key="sk_test", base_url=BASE, api_version=None)
    route = respx.post(f"{BASE}/v1/sdk/limits").mock(
        return_value=httpx.Response(200, json=_LIMITS_RESP)
    )
    sv.limits.check(customer_ref="cus_1", product_ref="prd_1")
    assert "Solvapay-Version" not in route.calls.last.request.headers


def test_default_api_version_matches_release_date() -> None:
    sv = SolvaPay(api_key="sk_test", base_url=BASE)
    # Default is threaded from SolvaPay → HttpClient → HttpxTransport
    assert sv._http._transport._api_version == "2026-05-22"


@respx.mock
async def test_async_api_version_header_sent() -> None:
    sv = AsyncSolvaPay(api_key="sk_test", base_url=BASE, api_version="2026-05-22")
    route = respx.post(f"{BASE}/v1/sdk/limits").mock(
        return_value=httpx.Response(200, json=_LIMITS_RESP)
    )
    await sv.limits.acheck(customer_ref="cus_1", product_ref="prd_1")
    assert route.calls.last.request.headers["Solvapay-Version"] == "2026-05-22"


@respx.mock
async def test_async_api_version_none_omits_header() -> None:
    sv = AsyncSolvaPay(api_key="sk_test", base_url=BASE, api_version=None)
    route = respx.post(f"{BASE}/v1/sdk/limits").mock(
        return_value=httpx.Response(200, json=_LIMITS_RESP)
    )
    await sv.limits.acheck(customer_ref="cus_1", product_ref="prd_1")
    assert "Solvapay-Version" not in route.calls.last.request.headers
