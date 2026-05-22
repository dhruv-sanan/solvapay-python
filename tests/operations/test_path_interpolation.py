"""Tests: _interpolate URL-safe path param substitution (HLD OR2)."""

from __future__ import annotations

from solvapay.operations._registry import _interpolate


def test_simple_substitution() -> None:
    assert _interpolate("/v1/sdk/customers/{customer_ref}", customer_ref="cus_abc") == "/v1/sdk/customers/cus_abc"


def test_slash_in_value_is_encoded() -> None:
    result = _interpolate("/v1/sdk/customers/{customer_ref}", customer_ref="cus/with/slash")
    assert "cus%2Fwith%2Fslash" in result
    assert "/" not in result.split("/v1/sdk/customers/")[1]


def test_question_mark_encoded() -> None:
    result = _interpolate("/v1/sdk/customers/{customer_ref}", customer_ref="cus?q=1")
    assert "%3F" in result


def test_hash_encoded() -> None:
    result = _interpolate("/v1/sdk/customers/{customer_ref}", customer_ref="cus#frag")
    assert "%23" in result


def test_space_encoded() -> None:
    result = _interpolate("/v1/sdk/customers/{customer_ref}", customer_ref="cus name")
    assert "%20" in result


def test_unicode_encoded() -> None:
    result = _interpolate("/v1/sdk/customers/{customer_ref}", customer_ref="cüs_123")
    # ü → %C3%BC in URL encoding
    assert "%C3%BC" in result
    assert "{customer_ref}" not in result


def test_multiple_params() -> None:
    result = _interpolate(
        "/v1/sdk/products/{product_ref}/plans/{plan_ref}",
        product_ref="prd_abc",
        plan_ref="pln_xyz",
    )
    assert result == "/v1/sdk/products/prd_abc/plans/pln_xyz"


def test_no_substitution_if_no_match() -> None:
    result = _interpolate("/v1/sdk/customers", customer_ref="unused")
    assert result == "/v1/sdk/customers"
