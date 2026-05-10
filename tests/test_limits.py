"""Tests for SolvaPay.check_limits."""
from __future__ import annotations

import json

import httpx
import respx

from solvapay import SolvaPay


@respx.mock
def test_check_limits_within_limits(client: SolvaPay) -> None:
    respx.post("https://api.solvapay.test/v1/sdk/limits").mock(
        return_value=httpx.Response(
            200, json={"withinLimits": True, "remaining": 5, "plan": "starter"}
        )
    )
    result = client.check_limits(customer_ref="cus_123", product_ref="prd_abc")
    assert result.within_limits is True
    assert result.remaining == 5
    assert result.plan == "starter"


@respx.mock
def test_check_limits_exceeded_returns_checkout_url(client: SolvaPay) -> None:
    respx.post("https://api.solvapay.test/v1/sdk/limits").mock(
        return_value=httpx.Response(
            200,
            json={
                "withinLimits": False,
                "remaining": 0,
                "checkoutUrl": "https://solvapay.com/c/upgrade",
            },
        )
    )
    result = client.check_limits(customer_ref="cus_123", product_ref="prd_abc")
    assert result.within_limits is False
    assert result.checkout_url == "https://solvapay.com/c/upgrade"


@respx.mock
def test_check_limits_optional_params_propagate(client: SolvaPay) -> None:
    route = respx.post("https://api.solvapay.test/v1/sdk/limits").mock(
        return_value=httpx.Response(200, json={"withinLimits": True, "remaining": 10})
    )
    client.check_limits(
        customer_ref="cus_123",
        product_ref="prd_abc",
        plan_ref="pln_starter",
        meter_name="api_calls",
        usage_type="metered",
    )
    body = json.loads(route.calls.last.request.read())
    assert body["planRef"] == "pln_starter"
    assert body["meterName"] == "api_calls"
    assert body["usageType"] == "metered"
