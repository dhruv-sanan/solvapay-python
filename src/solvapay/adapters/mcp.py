"""solvapay.adapters.mcp — framework-neutral payable_tool + four schema flavors (HLD V1.17).

Optional extra: pip install solvapay-python[mcp]  (requires fastmcp>=0.4,<0.5)

Four schema-flavor functions (HLD AD5 lock — no single payable_tool_schema()):
    payable_tool_mcp_schema(fn) -> dict           MCP inputSchema
    payable_tool_openai_function(fn) -> dict       OpenAI function-calling
    payable_tool_anthropic_tool(fn) -> dict        Anthropic input_schema
    payable_tool_langchain_args_schema(fn) -> type  LangChain BaseModel subclass
"""

from __future__ import annotations

import functools
import inspect
from typing import TYPE_CHECKING, Any, Literal

from solvapay.paywall.core import Paywall, PaywallRequired
from solvapay.paywall.meta import PayableToolMeta

if TYPE_CHECKING:
    pass


def payable_tool(
    *,
    product: str,
    customer_ref_arg: str = "customer_ref",
    plan: str | None = None,
    client: object | None = None,
    mode: Literal["raise", "return_dict"] = "return_dict",
) -> Any:
    """Stamp fn.__solvapay_meta__ and wrap with Paywall/AsyncPaywall gate.

    Rejects bound methods, classmethods, staticmethods (HLD AD2).
    """

    def decorator(fn: Any) -> Any:
        if isinstance(fn, (classmethod, staticmethod)):
            raise TypeError("payable_tool cannot wrap classmethod or staticmethod")
        if hasattr(fn, "__self__"):
            raise TypeError("payable_tool cannot wrap bound methods")

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            from solvapay._async_client import AsyncSolvaPay as _AsyncSolvaPay
            from solvapay.client import SolvaPay as _SolvaPay

            sv = client
            if sv is None or (not isinstance(sv, _SolvaPay) and not isinstance(sv, _AsyncSolvaPay)):
                sv = _SolvaPay()

            pw = Paywall(client=sv, product=product, plan=plan, customer_ref_arg=customer_ref_arg)
            try:
                pw.gate(*args, **kwargs)
            except PaywallRequired as exc:
                if mode == "raise":
                    raise
                return {
                    "paywall_required": True,
                    "checkout_url": exc.checkout_url,
                }
            return fn(*args, **kwargs)

        wrapper.__solvapay_meta__ = PayableToolMeta(  # type: ignore[attr-defined]
            product=product,
            plan=plan,
            customer_ref_resolver=customer_ref_arg,
        )
        return wrapper

    return decorator


def register_payable_tool_fastmcp(mcp_server: Any, fn: Any) -> None:
    """Register a @payable_tool-decorated function with a FastMCP server.

    Requires: pip install solvapay-python[mcp]
    """
    try:
        import fastmcp  # noqa: F401
    except ImportError as exc:
        raise ImportError("fastmcp is required: pip install 'solvapay-python[mcp]'") from exc

    mcp_server.tool()(fn)


# ── Four schema-flavor functions (HLD AD5 lock) ──


def payable_tool_mcp_schema(fn: Any) -> dict[str, Any]:
    """Return MCP-format inputSchema for a @payable_tool-decorated function."""
    return _pydantic_json_schema(fn, mode="mcp")


def payable_tool_openai_function(fn: Any) -> dict[str, Any]:
    """Return OpenAI function-calling schema for a @payable_tool-decorated function."""
    schema = _pydantic_json_schema(fn, mode="openai")
    return {
        "name": fn.__name__,
        "description": (fn.__doc__ or "").strip(),
        "parameters": schema,
    }


def payable_tool_anthropic_tool(fn: Any) -> dict[str, Any]:
    """Return Anthropic tool schema for a @payable_tool-decorated function."""
    schema = _pydantic_json_schema(fn, mode="anthropic")
    return {
        "name": fn.__name__,
        "description": (fn.__doc__ or "").strip(),
        "input_schema": schema,
    }


def payable_tool_langchain_args_schema(fn: Any) -> type:
    """Return a Pydantic BaseModel subclass from the function signature.

    Requires: pydantic>=2.6
    """
    try:
        from pydantic import create_model
    except ImportError as exc:
        raise ImportError("pydantic>=2.6 is required") from exc

    sig = inspect.signature(fn)
    fields: dict[str, Any] = {}
    for name, param in sig.parameters.items():
        if name == "self":
            continue
        annotation = param.annotation if param.annotation is not inspect.Parameter.empty else Any
        default = param.default if param.default is not inspect.Parameter.empty else ...
        fields[name] = (annotation, default)

    return create_model(f"{fn.__name__}_ArgsSchema", **fields)


def _pydantic_json_schema(fn: Any, mode: str) -> dict[str, Any]:
    """Extract JSON schema from function signature via pydantic."""
    try:
        from pydantic import create_model
        from pydantic.json_schema import model_json_schema
    except ImportError as exc:
        raise ImportError("pydantic>=2.6 is required") from exc

    sig = inspect.signature(fn)
    fields: dict[str, Any] = {}
    for name, param in sig.parameters.items():
        if name == "self":
            continue
        annotation = param.annotation if param.annotation is not inspect.Parameter.empty else Any
        default = param.default if param.default is not inspect.Parameter.empty else ...
        fields[name] = (annotation, default)

    model = create_model(f"{fn.__name__}_Schema", **fields)
    return model_json_schema(model)
