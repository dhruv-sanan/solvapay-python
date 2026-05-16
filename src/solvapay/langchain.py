"""Optional LangChain integration. Requires `pip install solvapay[langchain]`."""

from __future__ import annotations

from functools import wraps
from typing import Any

try:
    from langchain_core.tools import BaseTool
except ImportError as exc:
    raise ImportError(
        "LangChain is not installed. Run: pip install solvapay[langchain]"
    ) from exc

from solvapay.client import SolvaPay
from solvapay.paywall_state import decide


def monetize_tool(
    tool: BaseTool,
    *,
    product: str,
    customer_ref_arg: str = "customer_ref",
    client: SolvaPay | None = None,
) -> BaseTool:
    """Wrap a LangChain tool with SolvaPay paywall gating.

    Checks check_limits before each invocation. On gate hit, returns a
    structured dict with the checkout URL — does NOT raise — so LangChain
    agents can surface the recovery action to the user.

    Args:
        tool: Any LangChain BaseTool (Tool, StructuredTool, etc.).
        product: SolvaPay product reference (e.g., "prd_0QKI8NHF").
        customer_ref_arg: Name of the kwarg carrying the customer ref.
        client: Pre-configured SolvaPay instance. Constructs one per call if omitted.

    Returns:
        The same tool with its `.func` replaced by a gated wrapper.

    Example:
        from langchain_core.tools import Tool
        from solvapay.langchain import monetize_tool

        raw = Tool.from_function(name="search", func=do_search, description="Search the web.")
        paid = monetize_tool(raw, product="prd_search")
    """
    sv = client or SolvaPay()
    original_func = tool.func  # type: ignore[attr-defined]

    @wraps(original_func)
    def gated(**kwargs: Any) -> Any:
        customer_ref = kwargs.get(customer_ref_arg)
        if not isinstance(customer_ref, str):
            return {"error": f"Missing required argument: {customer_ref_arg}"}
        limits = sv.check_limits(customer_ref=customer_ref, product_ref=product)
        if not limits.within_limits:
            d = decide(limits)
            return {
                "paywall_required": True,
                "state": d.state.value,
                "message": d.message,
                "checkout_url": d.checkout_url,
                "recovery_tool": d.recovery_tool,
            }
        return original_func(**kwargs)

    tool.func = gated  # type: ignore[attr-defined]
    return tool
