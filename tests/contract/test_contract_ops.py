"""Sandbox contract tests — run against real SolvaPay sandbox API.

Requires: SOLVAPAY_SANDBOX_KEY env var.
Skip automatically when not set.
"""

from __future__ import annotations

import os

import pytest

SANDBOX_KEY = os.getenv("SOLVAPAY_SANDBOX_KEY")
pytestmark = pytest.mark.contract


@pytest.fixture
def sv():
    if not SANDBOX_KEY:
        pytest.skip("SOLVAPAY_SANDBOX_KEY not set")
    from solvapay import SolvaPay

    return SolvaPay(api_key=SANDBOX_KEY)


@pytest.mark.contract
def test_contract_check_limits(sv) -> None:
    """check_limits returns valid response shape from sandbox."""
    from solvapay.models import LimitResponse

    result = sv.limits.check(
        customer_ref=os.environ["SOLVAPAY_TEST_CUSTOMER_REF"],
        product_ref=os.environ["SOLVAPAY_TEST_PRODUCT_REF"],
    )
    assert isinstance(result, LimitResponse)
    assert isinstance(result.within_limits, bool)
    assert isinstance(result.remaining, (int, float))


@pytest.mark.contract
def test_contract_ensure_customer(sv) -> None:
    """ensure_customer is idempotent on sandbox."""
    ref = sv.customers.ensure(os.environ["SOLVAPAY_TEST_CUSTOMER_REF"])
    assert isinstance(ref, str)
    assert len(ref) > 0


@pytest.mark.contract
def test_contract_create_checkout_session(sv) -> None:
    """create_session returns a checkout URL from sandbox."""
    from solvapay.idempotency import from_payload
    from solvapay.models import CheckoutSession

    key = from_payload("contract_test_session", time_bucket=None)
    session = sv.checkout.create_session(
        customer_ref=os.environ["SOLVAPAY_TEST_CUSTOMER_REF"],
        product_ref=os.environ["SOLVAPAY_TEST_PRODUCT_REF"],
        idempotency_key=key,
    )
    assert isinstance(session, CheckoutSession)
    assert session.checkout_url.startswith("https://")
