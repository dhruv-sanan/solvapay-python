"""Tests: Paywall/AsyncPaywall split (HLD V1.6 PW1)."""

from __future__ import annotations

import pytest

from solvapay.paywall.core import AsyncPaywall, Paywall, PaywallRequired


def test_paywall_requires_sync_client() -> None:
    from solvapay._async_client import AsyncSolvaPay

    with pytest.raises(TypeError, match="SolvaPay"):
        Paywall(client=AsyncSolvaPay(api_key="sk_test"), product="prd_x")  # type: ignore[arg-type]


def test_async_paywall_requires_async_client() -> None:
    from solvapay.client import SolvaPay

    with pytest.raises(TypeError, match="AsyncSolvaPay"):
        AsyncPaywall(client=SolvaPay(api_key="sk_test"), product="prd_x")  # type: ignore[arg-type]


def test_paywall_required_has_checkout_mint_error_field() -> None:
    exc = PaywallRequired(checkout_url=None)
    assert exc.checkout_mint_error is None


def test_paywall_required_checkout_mint_error_is_set() -> None:
    from solvapay.exceptions import APIError

    err = APIError(503, "mint failed")
    exc = PaywallRequired(checkout_url=None, checkout_mint_error=err)
    assert exc.checkout_mint_error is err
