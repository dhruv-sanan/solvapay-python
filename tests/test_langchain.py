"""Tests for solvapay.langchain — monetize_tool decorator."""

from __future__ import annotations

from unittest.mock import MagicMock

from solvapay import SolvaPay
from solvapay.models import LimitResponse
from solvapay.langchain import monetize_tool


def _mock_client(
    *,
    within_limits: bool,
    checkout_url: str | None = None,
    plan: str | None = "pln_basic",
) -> SolvaPay:
    client = MagicMock(spec=SolvaPay)
    client.check_limits.return_value = LimitResponse(
        within_limits=within_limits,
        remaining=5 if within_limits else 0,
        checkout_url=checkout_url,
        plan=plan,
    )
    return client


def _make_tool(func: object) -> object:
    """Build a minimal mock that looks like a LangChain BaseTool."""
    tool = MagicMock()
    tool.func = func
    return tool


def test_passthrough_when_within_limits() -> None:
    def do_search(*, customer_ref: str, query: str) -> str:
        return f"results for {query}"

    client = _mock_client(within_limits=True)
    tool = _make_tool(do_search)
    monetize_tool(tool, product="prd_search", client=client)  # type: ignore[arg-type]

    result = tool.func(customer_ref="cus_123", query="langchain")
    assert result == "results for langchain"
    client.check_limits.assert_called_once_with(customer_ref="cus_123", product_ref="prd_search")


def test_returns_paywall_dict_when_gated() -> None:
    def do_search(*, customer_ref: str, query: str) -> str:
        return "should not reach"

    client = _mock_client(within_limits=False, checkout_url="https://solvapay.com/c/upgrade")
    tool = _make_tool(do_search)
    monetize_tool(tool, product="prd_search", client=client)  # type: ignore[arg-type]

    result = tool.func(customer_ref="cus_123", query="anything")
    assert isinstance(result, dict)
    assert result["paywall_required"] is True
    assert result["checkout_url"] == "https://solvapay.com/c/upgrade"
    assert result["recovery_tool"] == "upgrade"
    assert "message" in result


def test_missing_customer_ref_returns_error() -> None:
    def do_search(*, query: str) -> str:
        return "results"

    client = _mock_client(within_limits=True)
    tool = _make_tool(do_search)
    monetize_tool(tool, product="prd_search", client=client)  # type: ignore[arg-type]

    result = tool.func(query="no ref here")
    assert isinstance(result, dict)
    assert "error" in result
    assert "customer_ref" in result["error"]
    client.check_limits.assert_not_called()
