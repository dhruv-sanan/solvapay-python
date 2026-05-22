"""Tests: resource-namespace API parity with deprecated flat shims."""

from __future__ import annotations

import warnings

import httpx
import respx

from solvapay import SolvaPay

BASE = "https://api.solvapay.test"
CUSTOMER_RESPONSE = {"reference": "cus_abc", "purchases": []}


@respx.mock
def test_namespace_customers_get_returns_same_as_flat(client: SolvaPay) -> None:
    respx.get(f"{BASE}/v1/sdk/customers/cus_abc").mock(
        return_value=httpx.Response(200, json=CUSTOMER_RESPONSE)
    )
    ns_result = client.customers.get("cus_abc")
    assert ns_result.customer_ref == "cus_abc"


@respx.mock
def test_flat_shim_emits_deprecation_warning(client: SolvaPay) -> None:
    respx.get(f"{BASE}/v1/sdk/customers/cus_abc").mock(
        return_value=httpx.Response(200, json=CUSTOMER_RESPONSE)
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        client.get_customer("cus_abc")
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)


@respx.mock
def test_namespace_and_flat_return_identical_result(client: SolvaPay) -> None:
    respx.get(f"{BASE}/v1/sdk/customers/cus_abc").mock(
        return_value=httpx.Response(200, json=CUSTOMER_RESPONSE)
    )
    ns = client.customers.get("cus_abc")
    flat = client.get_customer("cus_abc")
    assert ns.customer_ref == flat.customer_ref
    assert ns.customer_ref == "cus_abc"


@respx.mock
def test_sv_has_all_namespace_attrs(client: SolvaPay) -> None:
    for attr in (
        "customers",
        "checkout",
        "limits",
        "purchases",
        "usage",
        "products",
        "plans",
        "merchant",
    ):
        assert hasattr(client, attr), f"SolvaPay missing namespace: {attr}"
