"""Tests for SolvaPay.ensure_customer and get_customer."""
from __future__ import annotations

import httpx
import pytest
import respx

from solvapay import SolvaPay, SolvaPayAPIError


@respx.mock
def test_ensure_customer_returns_existing_ref_on_200(client: SolvaPay) -> None:
    respx.get("https://api.solvapay.test/v1/sdk/customers").mock(
        return_value=httpx.Response(200, json={"customerRef": "cus_existing"})
    )
    ref = client.ensure_customer("user_42")
    assert ref == "cus_existing"


@respx.mock
def test_ensure_customer_creates_on_404(client: SolvaPay) -> None:
    respx.get("https://api.solvapay.test/v1/sdk/customers").mock(
        return_value=httpx.Response(404, text="not found")
    )
    respx.post("https://api.solvapay.test/v1/sdk/customers").mock(
        return_value=httpx.Response(200, json={"customerRef": "cus_new"})
    )
    ref = client.ensure_customer("user_42")
    assert ref == "cus_new"


@respx.mock
def test_ensure_customer_reraises_non_404_error(client: SolvaPay) -> None:
    respx.get("https://api.solvapay.test/v1/sdk/customers").mock(
        return_value=httpx.Response(500, text="server error")
    )
    with pytest.raises(SolvaPayAPIError) as exc_info:
        client.ensure_customer("user_42")
    assert exc_info.value.status_code == 500


@respx.mock
def test_ensure_customer_auto_generates_email(client: SolvaPay) -> None:
    respx.get("https://api.solvapay.test/v1/sdk/customers").mock(
        return_value=httpx.Response(404, text="not found")
    )
    post_route = respx.post("https://api.solvapay.test/v1/sdk/customers").mock(
        return_value=httpx.Response(200, json={"customerRef": "cus_new"})
    )
    client.ensure_customer("user_42")
    import json

    body = json.loads(post_route.calls.last.request.read())
    assert "@auto-created.local" in body["email"]
    assert body["externalRef"] == "user_42"


@respx.mock
def test_ensure_customer_uses_explicit_email(client: SolvaPay) -> None:
    respx.get("https://api.solvapay.test/v1/sdk/customers").mock(
        return_value=httpx.Response(404, text="not found")
    )
    post_route = respx.post("https://api.solvapay.test/v1/sdk/customers").mock(
        return_value=httpx.Response(200, json={"customerRef": "cus_new"})
    )
    client.ensure_customer("user_42", email="user@example.com")
    import json

    body = json.loads(post_route.calls.last.request.read())
    assert body["email"] == "user@example.com"


@respx.mock
def test_get_customer_by_ref_hits_path(client: SolvaPay) -> None:
    route = respx.get("https://api.solvapay.test/v1/sdk/customers/cus_abc").mock(
        return_value=httpx.Response(
            200,
            json={"customerRef": "cus_abc", "email": "a@b.com", "externalRef": "ext_1"},
        )
    )
    customer = client.get_customer("cus_abc")
    assert route.called
    assert customer.customer_ref == "cus_abc"


@respx.mock
def test_get_customer_by_external_ref_uses_query_string(client: SolvaPay) -> None:
    route = respx.get("https://api.solvapay.test/v1/sdk/customers").mock(
        return_value=httpx.Response(200, json={"customerRef": "cus_abc", "externalRef": "ext_1"})
    )
    client.get_customer(external_ref="ext_1")
    assert route.called
    assert route.calls.last.request.url.params["externalRef"] == "ext_1"


@respx.mock
def test_get_customer_by_email_uses_query_string(client: SolvaPay) -> None:
    respx.get("https://api.solvapay.test/v1/sdk/customers").mock(
        return_value=httpx.Response(200, json={"customerRef": "cus_abc", "email": "a@b.com"})
    )
    customer = client.get_customer(email="a@b.com")
    assert customer.customer_ref == "cus_abc"


def test_get_customer_raises_if_no_params(client: SolvaPay) -> None:
    with pytest.raises(ValueError, match="Must provide"):
        client.get_customer()
