"""LangChain adapter — protocol-based duck-typing + Paywall composition (HLD V1.8).

Does NOT hard-import langchain_core at module level (absorbs 0.3→0.4 churn).
Uses Protocol duck-typing; lazy-imports BaseTool only for isinstance fallback.

Optional: pip install solvapay-python[langchain]
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Protocol, runtime_checkable

from solvapay.paywall.core import Paywall, PaywallRequired


@runtime_checkable
class LangChainToolProtocol(Protocol):
    """Duck-type contract for LangChain tools (BaseTool-like)."""

    name: str
    description: str

    def _run(self, *args: Any, **kwargs: Any) -> Any: ...

    async def _arun(self, *args: Any, **kwargs: Any) -> Any: ...


def monetize_tool(
    tool: Any,
    *,
    product: str,
    customer_ref_arg: str = "customer_ref",
    client: Any | None = None,
) -> Any:
    """Wrap any LangChain tool (or LangChainToolProtocol-compatible object) with a paywall gate.

    Reads fn.__solvapay_meta__ if present. On gate hit returns a structured dict
    (does NOT raise) so agents can surface the checkout URL (HLD V1.8).

    Lazy-imports langchain_core.tools.BaseTool only for isinstance fallback.
    """
    from solvapay.client import SolvaPay
    from solvapay.paywall_state import decide

    sv = client if client is not None else SolvaPay()

    # Read __solvapay_meta__ if stamped by @payable_tool
    meta = getattr(tool, "__solvapay_meta__", None)
    if meta is not None:
        effective_product = getattr(meta, "product", product)
        effective_resolver = getattr(meta, "customer_ref_resolver", customer_ref_arg)
    else:
        effective_product = product
        effective_resolver = customer_ref_arg

    # Try to get underlying callable
    original_func = getattr(tool, "func", None) or tool

    @wraps(original_func)
    def gated(**kwargs: Any) -> Any:
        customer_ref = kwargs.get(effective_resolver)
        if not isinstance(customer_ref, str):
            return {"error": f"Missing required argument: {effective_resolver}"}

        pw = Paywall(client=sv, product=effective_product, customer_ref_arg=effective_resolver)
        try:
            pw.gate(**kwargs)
        except PaywallRequired as exc:
            limits = sv.limits.check(
                customer_ref=customer_ref,
                product_ref=effective_product,
            )
            d = decide(limits)
            return {
                "paywall_required": True,
                "state": d.state.value,
                "message": d.message,
                "checkout_url": exc.checkout_url or d.checkout_url,
                "recovery_tool": d.recovery_tool,
            }
        return original_func(**kwargs)

    if hasattr(tool, "func"):
        tool.func = gated
        return tool

    return gated
