"""Tests for solvapay.langchain (shim) + solvapay.adapters.langchain."""

from __future__ import annotations

from unittest.mock import MagicMock

from solvapay.adapters.langchain import monetize_tool
from solvapay.models import LimitResponse


def _mock_client(
    *,
    within_limits: bool,
    checkout_url: str | None = None,
    plan: str | None = "pln_basic",
) -> object:
    client = MagicMock()
    client.limits.check.return_value = LimitResponse(
        within_limits=within_limits,
        remaining=5 if within_limits else 0,
        checkout_url=checkout_url,
        plan=plan,
    )
    # checkout for mint when blocked
    from solvapay.models import CheckoutSession
    client.checkout.create_session.return_value = CheckoutSession(
        session_id="s", checkout_url=checkout_url or "https://checkout.solvapay.com/x"
    )
    return client


def _make_tool(func: object) -> object:
    tool = MagicMock()
    tool.func = func
    return tool


def test_passthrough_when_within_limits() -> None:
    def do_search(*, customer_ref: str, query: str) -> str:
        return f"results for {query}"

    client = _mock_client(within_limits=True)
    tool = _make_tool(do_search)
    monetize_tool(tool, product="prd_search", client=client)

    result = tool.func(customer_ref="cus_123", query="langchain")
    assert result == "results for langchain"
    client.limits.check.assert_called_once_with(
        customer_ref="cus_123", product_ref="prd_search", plan_ref=None
    )


def test_returns_paywall_dict_when_gated() -> None:
    def do_search(*, customer_ref: str, query: str) -> str:
        return "should not reach"

    client = _mock_client(
        within_limits=False, checkout_url="https://solvapay.com/c/upgrade", plan="pln_basic"
    )
    tool = _make_tool(do_search)
    monetize_tool(tool, product="prd_search", client=client)

    result = tool.func(customer_ref="cus_123", query="anything")
    assert isinstance(result, dict)
    assert result["paywall_required"] is True


def test_missing_customer_ref_returns_error() -> None:
    def do_search(*, query: str) -> str:
        return "results"

    client = _mock_client(within_limits=True)
    tool = _make_tool(do_search)
    monetize_tool(tool, product="prd_search", client=client)

    result = tool.func(query="no ref here")
    assert isinstance(result, dict)
    assert "error" in result
    assert "customer_ref" in result["error"]
    client.limits.check.assert_not_called()
