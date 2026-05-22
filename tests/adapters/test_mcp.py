"""Tests: solvapay.adapters.mcp — payable_tool + four schema flavors (HLD V1.17)."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest
import respx

from solvapay import SolvaPay
from solvapay.adapters.mcp import (
    payable_tool,
    payable_tool_anthropic_tool,
    payable_tool_langchain_args_schema,
    payable_tool_mcp_schema,
    payable_tool_openai_function,
    register_payable_tool_fastmcp,
)
from solvapay.paywall.core import PaywallRequired
from solvapay.paywall.meta import PayableToolMeta

BASE = "https://api.solvapay.test"


def test_payable_tool_stamps_meta_with_version_1() -> None:
    @payable_tool(product="prd_x")
    def my_fn(*, customer_ref: str) -> str:
        return customer_ref

    meta = my_fn.__solvapay_meta__  # type: ignore[attr-defined]
    assert isinstance(meta, PayableToolMeta)
    assert meta._meta_version == 1
    assert meta.product == "prd_x"


def test_payable_tool_preserves_signature_via_functools_wraps() -> None:
    @payable_tool(product="prd_x")
    def compute(*, customer_ref: str, value: int) -> int:
        """Computes something."""
        return value

    assert compute.__name__ == "compute"
    assert compute.__doc__ == "Computes something."
    assert hasattr(compute, "__wrapped__")


@respx.mock
def test_payable_tool_passes_through_on_within_limits() -> None:
    sv = SolvaPay(api_key="sk_test_dummy", base_url=BASE)
    respx.post(f"{BASE}/v1/sdk/limits").mock(
        return_value=httpx.Response(200, json={"withinLimits": True, "remaining": 10})
    )

    @payable_tool(product="prd_x", client=sv)
    def run(*, customer_ref: str) -> str:
        return "ok"

    assert run(customer_ref="cus_abc") == "ok"


@respx.mock
def test_payable_tool_return_dict_mode_on_gate_hit() -> None:
    sv = SolvaPay(api_key="sk_test_dummy", base_url=BASE)
    respx.post(f"{BASE}/v1/sdk/limits").mock(
        return_value=httpx.Response(200, json={"withinLimits": False, "remaining": 0})
    )
    respx.post(f"{BASE}/v1/sdk/checkout-sessions").mock(
        return_value=httpx.Response(
            200, json={"sessionId": "s", "checkoutUrl": "https://checkout.solvapay.com/x"}
        )
    )

    @payable_tool(product="prd_x", client=sv, mode="return_dict")
    def run(*, customer_ref: str) -> str:
        return "ok"

    result = run(customer_ref="cus_abc")
    assert result["paywall_required"] is True
    assert result["checkout_url"] == "https://checkout.solvapay.com/x"


@respx.mock
def test_payable_tool_raise_mode_on_gate_hit() -> None:
    sv = SolvaPay(api_key="sk_test_dummy", base_url=BASE)
    respx.post(f"{BASE}/v1/sdk/limits").mock(
        return_value=httpx.Response(200, json={"withinLimits": False, "remaining": 0})
    )
    respx.post(f"{BASE}/v1/sdk/checkout-sessions").mock(
        return_value=httpx.Response(
            200, json={"sessionId": "s", "checkoutUrl": "https://checkout.solvapay.com/x"}
        )
    )

    @payable_tool(product="prd_x", client=sv, mode="raise")
    def run(*, customer_ref: str) -> str:
        return "ok"

    with pytest.raises(PaywallRequired):
        run(customer_ref="cus_abc")


def test_register_payable_tool_fastmcp_calls_fastmcp_register() -> None:
    mcp_server = MagicMock()
    mcp_server.tool.return_value = lambda fn: fn

    @payable_tool(product="prd_x")
    def fn(*, customer_ref: str) -> str:
        return customer_ref

    try:
        register_payable_tool_fastmcp(mcp_server, fn)
        mcp_server.tool.assert_called_once()
    except ImportError:
        pytest.skip("fastmcp not installed")


def test_payable_tool_rejects_bound_methods() -> None:
    class _Obj:
        def method(self) -> None: ...

    obj = _Obj()
    with pytest.raises(TypeError, match="bound method"):
        payable_tool(product="prd_x")(obj.method)  # type: ignore[arg-type]


def test_payable_tool_rejects_classmethods() -> None:
    cm: object = classmethod(lambda cls: None)
    with pytest.raises(TypeError, match="classmethod"):
        payable_tool(product="prd_x")(cm)  # type: ignore[arg-type]


def test_payable_tool_rejects_staticmethods() -> None:
    sm: object = staticmethod(lambda: None)
    with pytest.raises(TypeError):
        payable_tool(product="prd_x")(sm)  # type: ignore[arg-type]


def test_four_schema_flavors_each_return_correct_shape() -> None:
    @payable_tool(product="prd_x")
    def search(*, customer_ref: str, query: str, max_results: int = 5) -> list[str]:
        """Search the web."""
        return []

    # MCP schema
    mcp = payable_tool_mcp_schema(search)
    assert "properties" in mcp
    assert "query" in mcp["properties"]

    # OpenAI function
    openai = payable_tool_openai_function(search)
    assert openai["name"] == "search"
    assert "parameters" in openai
    assert openai["parameters"]["properties"]["query"]

    # Anthropic tool
    anthropic = payable_tool_anthropic_tool(search)
    assert anthropic["name"] == "search"
    assert "input_schema" in anthropic
    assert anthropic["input_schema"]["properties"]["query"]

    # LangChain args schema
    schema_model = payable_tool_langchain_args_schema(search)
    assert hasattr(schema_model, "model_fields")
    assert "query" in schema_model.model_fields
