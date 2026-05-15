"""Tests for @paywall.require decorator."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from solvapay import SolvaPay, SolvaPayError
from solvapay.models import LimitResponse
from solvapay.paywall import PaywallRequired, require


def _mock_client(*, within_limits: bool, checkout_url: str | None = None) -> SolvaPay:
    client = MagicMock(spec=SolvaPay)
    client.check_limits.return_value = LimitResponse(
        within_limits=within_limits,
        remaining=5 if within_limits else 0,
        checkout_url=checkout_url,
    )
    return client


def test_passes_through_when_within_limits() -> None:
    client = _mock_client(within_limits=True)

    @require(product="prd_abc", client=client)
    def run(*, customer_ref: str) -> str:
        return "result"

    assert run(customer_ref="cus_123") == "result"
    client.check_limits.assert_called_once_with(
        customer_ref="cus_123", product_ref="prd_abc", plan_ref=None
    )


def test_raises_paywall_required_when_exceeded() -> None:
    client = _mock_client(within_limits=False, checkout_url="https://solvapay.com/c/upgrade")

    @require(product="prd_abc", client=client)
    def run(*, customer_ref: str) -> str:
        return "result"

    with pytest.raises(PaywallRequired) as exc_info:
        run(customer_ref="cus_123")

    assert exc_info.value.checkout_url == "https://solvapay.com/c/upgrade"


def test_paywall_required_inherits_solvapay_error() -> None:
    err = PaywallRequired(checkout_url="https://example.com")
    assert isinstance(err, SolvaPayError)


def test_raises_if_customer_ref_arg_missing() -> None:
    client = _mock_client(within_limits=True)

    @require(product="prd_abc", client=client)
    def run(*, name: str) -> str:
        return name

    with pytest.raises(SolvaPayError, match="expected str kwarg"):
        run(name="alice")  # type: ignore[call-arg]


def test_custom_customer_ref_arg_name() -> None:
    client = _mock_client(within_limits=True)

    @require(product="prd_abc", client=client, customer_ref_arg="user_id")
    def run(*, user_id: str) -> str:
        return user_id

    assert run(user_id="cus_xyz") == "cus_xyz"
    client.check_limits.assert_called_once_with(
        customer_ref="cus_xyz", product_ref="prd_abc", plan_ref=None
    )


def test_plan_ref_forwarded_to_check_limits() -> None:
    client = _mock_client(within_limits=True)

    @require(product="prd_abc", plan="pln_starter", client=client)
    def run(*, customer_ref: str) -> None:
        pass

    run(customer_ref="cus_123")
    client.check_limits.assert_called_once_with(
        customer_ref="cus_123", product_ref="prd_abc", plan_ref="pln_starter"
    )
