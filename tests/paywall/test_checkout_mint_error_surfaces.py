"""Tests: checkout_mint_error surfaces on mint failure (HLD V1.6 PW3)."""

from __future__ import annotations

import httpx
import pytest
import respx

from solvapay import SolvaPay
from solvapay.paywall.core import Paywall, PaywallRequired

BASE = "https://api.solvapay.test"


@respx.mock
def test_checkout_mint_error_set_when_mint_fails() -> None:
    sv = SolvaPay(api_key="sk_test_dummy", base_url=BASE)
    # limits says blocked, no checkout_url
    respx.post(f"{BASE}/v1/sdk/limits").mock(
        return_value=httpx.Response(200, json={"withinLimits": False, "remaining": 0})
    )
    # checkout session creation fails with 503
    respx.post(f"{BASE}/v1/sdk/checkout-sessions").mock(
        return_value=httpx.Response(503, text="unavailable")
    )

    pw = Paywall(client=sv, product="prd_x")
    with pytest.raises(PaywallRequired) as exc_info:
        pw.gate(customer_ref="cus_abc")

    assert exc_info.value.checkout_mint_error is not None
    assert exc_info.value.checkout_url is None


@respx.mock
def test_checkout_mint_error_none_when_mint_succeeds() -> None:
    sv = SolvaPay(api_key="sk_test_dummy", base_url=BASE)
    respx.post(f"{BASE}/v1/sdk/limits").mock(
        return_value=httpx.Response(200, json={"withinLimits": False, "remaining": 0})
    )
    respx.post(f"{BASE}/v1/sdk/checkout-sessions").mock(
        return_value=httpx.Response(
            200, json={"sessionId": "sess_x", "checkoutUrl": "https://checkout.solvapay.com/x"}
        )
    )

    pw = Paywall(client=sv, product="prd_x")
    with pytest.raises(PaywallRequired) as exc_info:
        pw.gate(customer_ref="cus_abc")

    assert exc_info.value.checkout_mint_error is None
    assert exc_info.value.checkout_url == "https://checkout.solvapay.com/x"
