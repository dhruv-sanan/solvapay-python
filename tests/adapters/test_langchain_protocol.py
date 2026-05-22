"""Tests: LangChain adapter protocol-based duck-typing (HLD V1.8)."""

from __future__ import annotations

import httpx
import respx

from solvapay import SolvaPay
from solvapay.adapters.langchain import LangChainToolProtocol, monetize_tool

BASE = "https://api.solvapay.test"


class MyTool:
    """Fake LangChain-like tool — no langchain_core import."""

    name = "my_tool"
    description = "Does something."

    def __init__(self) -> None:
        self._calls: list[dict] = []

    def _run(self, **kwargs: object) -> str:
        self._calls.append(dict(kwargs))
        return "result"

    async def _arun(self, **kwargs: object) -> str:
        return "async_result"

    def __call__(self, **kwargs: object) -> str:
        return self._run(**kwargs)

    @property
    def func(self) -> object:
        return self._run

    @func.setter
    def func(self, value: object) -> None:
        self._run = value  # type: ignore[assignment]


def test_my_tool_satisfies_protocol() -> None:
    assert isinstance(MyTool(), LangChainToolProtocol)


@respx.mock
def test_monetize_tool_passes_through_when_within_limits() -> None:
    sv = SolvaPay(api_key="sk_test_dummy", base_url=BASE)
    respx.post(f"{BASE}/v1/sdk/limits").mock(
        return_value=httpx.Response(200, json={"withinLimits": True, "remaining": 10})
    )

    tool = MyTool()
    monetized = monetize_tool(tool, product="prd_x", client=sv)
    result = monetized.func(customer_ref="cus_abc", query="hello")  # type: ignore[call-arg]
    assert result == "result"


@respx.mock
def test_monetize_tool_returns_dict_on_gate_hit() -> None:
    sv = SolvaPay(api_key="sk_test_dummy", base_url=BASE)
    respx.post(f"{BASE}/v1/sdk/limits").mock(
        return_value=httpx.Response(200, json={"withinLimits": False, "remaining": 0})
    )
    respx.post(f"{BASE}/v1/sdk/checkout-sessions").mock(
        return_value=httpx.Response(
            200, json={"sessionId": "s", "checkoutUrl": "https://checkout.solvapay.com/x"}
        )
    )
    # For decide() — second limits call
    respx.post(f"{BASE}/v1/sdk/limits").mock(
        return_value=httpx.Response(200, json={"withinLimits": False, "remaining": 0})
    )

    tool = MyTool()
    monetized = monetize_tool(tool, product="prd_x", client=sv)
    result = monetized.func(customer_ref="cus_abc")  # type: ignore[call-arg]
    assert result["paywall_required"] is True


def test_monetize_tool_works_without_langchain_core_installed() -> None:
    """Core functionality must not require langchain_core to be importable."""
    import sys

    # Temporarily hide langchain_core
    saved = sys.modules.get("langchain_core")
    sys.modules["langchain_core"] = None  # type: ignore[assignment]
    try:
        import importlib

        from solvapay.adapters import langchain as lc_mod

        importlib.reload(lc_mod)
        assert hasattr(lc_mod, "monetize_tool")
    finally:
        if saved is None:
            sys.modules.pop("langchain_core", None)
        else:
            sys.modules["langchain_core"] = saved
