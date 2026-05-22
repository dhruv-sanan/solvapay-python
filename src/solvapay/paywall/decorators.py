"""@require, @require_async, @payable_tool decorators."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from solvapay.exceptions import SolvaPayError
from solvapay.paywall.core import AsyncPaywall, Paywall, PaywallRequired

P = ParamSpec("P")
R = TypeVar("R")


def require(
    *,
    product: str,
    plan: str | None = None,
    customer_ref_arg: str = "customer_ref",
    client: object | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorate a sync function with a SolvaPay paywall check."""
    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            from solvapay.client import SolvaPay
            sv = client if client is not None else SolvaPay()
            pw = Paywall(client=sv, product=product, plan=plan, customer_ref_arg=customer_ref_arg)
            pw.gate(*args, **kwargs)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def require_async(
    *,
    product: str,
    plan: str | None = None,
    customer_ref_arg: str = "customer_ref",
    client: object | None = None,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Decorate an async function with a SolvaPay paywall check."""

    def decorator(fn: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            from solvapay._async_client import AsyncSolvaPay

            _owns_client = not isinstance(client, AsyncSolvaPay)
            sv: AsyncSolvaPay = AsyncSolvaPay() if _owns_client else client  # type: ignore[assignment]
            try:
                pw = AsyncPaywall(
                    client=sv, product=product, plan=plan, customer_ref_arg=customer_ref_arg
                )
                await pw.gate(*args, **kwargs)
                return await fn(*args, **kwargs)
            finally:
                if _owns_client:
                    await sv.aclose()

        return wrapper

    return decorator


def payable_tool(
    *,
    product: str,
    customer_ref_arg: str = "customer_ref",
    plan: str | None = None,
    client: object | None = None,
    mode: str = "return_dict",
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Stamp fn.__solvapay_meta__ with PayableToolMeta (HLD V1.17 AD1).

    Rejects bound methods, classmethods, staticmethods (HLD AD2).
    """
    from solvapay.paywall.meta import PayableToolMeta

    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        if isinstance(fn, (classmethod, staticmethod)):
            raise TypeError("payable_tool cannot wrap classmethod or staticmethod")
        if hasattr(fn, "__self__"):
            raise TypeError("payable_tool cannot wrap bound methods")

        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            from solvapay.client import SolvaPay
            from solvapay._async_client import AsyncSolvaPay

            customer_ref = kwargs.get(customer_ref_arg)
            if not isinstance(customer_ref, str):
                raise SolvaPayError(
                    f"payable_tool: expected str kwarg '{customer_ref_arg}', "
                    f"got {type(customer_ref).__name__}"
                )
            sv = client
            if isinstance(sv, AsyncSolvaPay):
                raise TypeError("Use the async variant of payable_tool for AsyncSolvaPay clients")
            if sv is None or not isinstance(sv, SolvaPay):
                sv = SolvaPay()
            pw = Paywall(client=sv, product=product, plan=plan, customer_ref_arg=customer_ref_arg)
            try:
                pw.gate(*args, **kwargs)
            except PaywallRequired as exc:
                if mode == "raise":
                    raise
                return {  # type: ignore[return-value]
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
