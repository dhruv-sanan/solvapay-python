"""Tests for SolvaPay.create_checkout_session."""

from __future__ import annotations

import json

import httpx
import respx

from solvapay import SolvaPay


@respx.mock
def test_create_checkout_session_sends_correct_request(client: SolvaPay) -> None:
    route = respx.post("https://api.solvapay.test/v1/sdk/checkout-sessions").mock(
        return_value=httpx.Response(
            200,
            json={"sessionId": "sess_abc", "checkoutUrl": "https://solvapay.com/c/abc"},
        )
    )

    session = client.create_checkout_session(
        customer_ref="cus_123",
        product_ref="prd_0QKI8NHF",
        plan_ref="pln_starter",
        return_url="https://example.com/done",
    )

    assert route.called
    assert route.calls.last.request.headers["authorization"] == "Bearer sk_test_dummy"
    body = json.loads(route.calls.last.request.read())
    assert body == {
        "customerRef": "cus_123",
        "productRef": "prd_0QKI8NHF",
        "planRef": "pln_starter",
        "returnUrl": "https://example.com/done",
    }
    assert session.session_id == "sess_abc"
    assert session.checkout_url == "https://solvapay.com/c/abc"


@respx.mock
def test_create_checkout_session_omits_optional_fields(client: SolvaPay) -> None:
    route = respx.post("https://api.solvapay.test/v1/sdk/checkout-sessions").mock(
        return_value=httpx.Response(200, json={"sessionId": "s", "checkoutUrl": "u"})
    )
    client.create_checkout_session(customer_ref="c", product_ref="p")
    body = json.loads(route.calls.last.request.read())
    assert body == {"customerRef": "c", "productRef": "p"}
    assert "planRef" not in body
    assert "returnUrl" not in body
