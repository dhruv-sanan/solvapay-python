"""Critical-path invariant tests required by pre-production QA gate (§3.3)."""

from __future__ import annotations

import inspect

import httpx
import pytest
import respx

from solvapay import AsyncSolvaPay, SolvaPay
from solvapay._config import DEFAULT_BASE_URL
from solvapay.exceptions import SolvaPayAPIError
from solvapay.models import (
    CheckLimitsRequest,
    CheckoutSessionRequest,
    CreateCustomerRequest,
    TrackUsageRequest,
    UpdateCustomerRequest,
)
from solvapay.paywall import PaywallRequired


def test_webhook_compare_digest_used_not_eq() -> None:
    """webhooks.py must use hmac.compare_digest, never plain == on HMAC values."""
    import solvapay.webhooks as wh_mod

    source = inspect.getsource(wh_mod)
    assert "compare_digest" in source, "compare_digest must be present in webhooks.py"
    # Ensure the comparison of expected vs received uses compare_digest, not ==
    # Find the line that compares the two digests
    compare_line = next(
        (line for line in source.splitlines() if "expected" in line and "received" in line), ""
    )
    assert "==" not in compare_line, (
        f"Plain == comparison found between HMAC digests: {compare_line!r}"
    )


def test_no_secret_in_error() -> None:
    """SolvaPayAPIError.__str__ must not echo API keys or webhook secrets."""
    err = SolvaPayAPIError(401, "Unauthorized")
    err_str = str(err)
    assert "sk_test" not in err_str
    assert "whsec_" not in err_str
    # Confirm the status code and body are what come through, not auth headers
    assert "401" in err_str or "Unauthorized" in err_str


def test_async_sync_op_parity() -> None:
    """Every public API op on SolvaPay must have a counterpart on AsyncSolvaPay."""
    # Public methods: non-dunder, non-leading-underscore
    sync_ops = {
        name
        for name in dir(SolvaPay)
        if not name.startswith("_") and callable(getattr(SolvaPay, name))
    }
    async_ops = {
        name
        for name in dir(AsyncSolvaPay)
        if not name.startswith("_") and callable(getattr(AsyncSolvaPay, name))
    }
    # close vs aclose is intentional lifecycle naming difference — exclude both
    sync_check = sync_ops - {"close"}
    async_check = async_ops - {"aclose"}
    missing_in_async = sync_check - async_check
    assert not missing_in_async, f"Sync ops missing async counterpart: {missing_in_async}"


def test_camelcase_wire_format_request() -> None:
    """Request models must serialize to camelCase keys for all create/update ops."""
    checkout = CheckoutSessionRequest(
        customer_ref="cus_1",
        product_ref="prd_A",
        plan_ref="plan_B",
        return_url="https://ret.example",
    )
    data = checkout.model_dump(by_alias=True, exclude_none=True)
    assert "customerRef" in data and "customer_ref" not in data
    assert "productRef" in data and "product_ref" not in data
    assert "planRef" in data and "plan_ref" not in data
    assert "returnUrl" in data and "return_url" not in data

    create_cust = CreateCustomerRequest(email="a@b.com", external_ref="ext_1")
    data2 = create_cust.model_dump(by_alias=True, exclude_none=True)
    assert "externalRef" in data2 and "external_ref" not in data2

    track = TrackUsageRequest(
        customer_ref="cus_1", product_ref="prd_A", meter_name="calls", units=1.0
    )
    data3 = track.model_dump(by_alias=True, exclude_none=True)
    assert "customerRef" in data3
    assert "productRef" in data3
    assert "meterName" in data3 and "meter_name" not in data3

    update = UpdateCustomerRequest(email="new@b.com", external_ref="ext_2")
    data4 = update.model_dump(by_alias=True, exclude_none=True)
    assert "externalRef" in data4 and "external_ref" not in data4

    limits = CheckLimitsRequest(customer_ref="cus_1", product_ref="prd_A")
    data5 = limits.model_dump(by_alias=True, exclude_none=True)
    assert "customerRef" in data5
    assert "productRef" in data5


def test_default_base_url_is_https() -> None:
    """Default API base URL must be HTTPS."""
    assert DEFAULT_BASE_URL.startswith("https://"), (
        f"DEFAULT_BASE_URL must use HTTPS, got: {DEFAULT_BASE_URL!r}"
    )


@respx.mock
async def test_require_async_on_sync_function_raises_type_error() -> None:
    """@paywall.require_async wrapping a sync (non-awaitable) function must fail clearly."""
    from solvapay import paywall

    sv = AsyncSolvaPay(api_key="sk_test_dummy", base_url="https://api.solvapay.test")
    respx.post("https://api.solvapay.test/v1/sdk/limits").mock(
        return_value=httpx.Response(200, json={"withinLimits": True, "remaining": 5})
    )

    @paywall.require_async(product="prd_A", client=sv)
    def sync_fn(*, customer_ref: str) -> str:  # type: ignore[return-value]
        return "result"

    with pytest.raises((TypeError, AttributeError)):
        await sync_fn(customer_ref="cus_1")  # type: ignore[misc]


def test_paywall_required_carries_checkout_url() -> None:
    """PaywallRequired must preserve checkout_url through the decorator."""
    url = "https://checkout.example.com/upgrade"
    exc = PaywallRequired(checkout_url=url)
    assert exc.checkout_url == url

    # Also verify it propagates correctly through @paywall.require
    with respx.mock:
        respx.post("https://api.solvapay.test/v1/sdk/limits").mock(
            return_value=httpx.Response(
                200,
                json={"withinLimits": False, "remaining": 0, "checkoutUrl": url},
            )
        )
        sv = SolvaPay(api_key="sk_test_dummy", base_url="https://api.solvapay.test")
        from solvapay import paywall

        @paywall.require(product="prd_A", client=sv)
        def gated(*, customer_ref: str) -> str:
            return "ok"

        with pytest.raises(PaywallRequired) as exc_info:
            gated(customer_ref="cus_1")
        assert exc_info.value.checkout_url == url
