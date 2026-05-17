"""Paywall decorator — wrap any function to auto-check limits before running.

Mirrors the @solvapay/server `payable` philosophy in a single decorator.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from solvapay.exceptions import SolvaPayError

P = ParamSpec("P")
R = TypeVar("R")


class PaywallRequired(SolvaPayError):
    """Raised by @paywall.require when a customer has exceeded their limits."""

    def __init__(self, checkout_url: str | None, message: str = "Paywall: limit exceeded") -> None:
        self.checkout_url = checkout_url
        super().__init__(message)


def require(
    *,
    product: str,
    plan: str | None = None,
    customer_ref_arg: str = "customer_ref",
    client: object | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorate a function with a SolvaPay paywall check.

    Before each call, checks `check_limits` for the customer. If
    `within_limits` is False, raises `PaywallRequired` with the checkout URL
    so the caller can redirect the user to upgrade.

    The decorated function must accept a `customer_ref` keyword argument
    (rename via `customer_ref_arg` if needed).

    Args:
        product: SolvaPay product reference (e.g., "prd_0QKI8NHF").
        plan: Optional plan reference to check against.
        customer_ref_arg: Name of the kwarg that carries the customer ref.
                          Defaults to "customer_ref".
        client: Pre-configured SolvaPay instance. If omitted, a new client
                is created per call (reads SOLVAPAY_SECRET_KEY from env).

    Example:
        sv = SolvaPay()

        @paywall.require(product="prd_0QKI8NHF", client=sv)
        def run_expensive_query(*, customer_ref: str, query: str) -> dict:
            ...
    """
    from solvapay.client import SolvaPay

    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            customer_ref = kwargs.get(customer_ref_arg)
            if not isinstance(customer_ref, str):
                raise SolvaPayError(
                    f"@paywall.require expected str kwarg '{customer_ref_arg}', "
                    f"got {type(customer_ref).__name__}"
                )
            sv: SolvaPay = client if isinstance(client, SolvaPay) else SolvaPay()
            limits = sv.check_limits(
                customer_ref=customer_ref,
                product_ref=product,
                plan_ref=plan,
            )
            if not limits.within_limits:
                checkout_url = limits.checkout_url
                if checkout_url is None:
                    try:
                        session = sv.create_checkout_session(
                            customer_ref=customer_ref, product_ref=product, plan_ref=plan
                        )
                        checkout_url = session.checkout_url
                    except SolvaPayError:
                        pass
                raise PaywallRequired(checkout_url=checkout_url)
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
    """Async equivalent of @paywall.require. Decorated function must be async.

    Args:
        product: SolvaPay product reference (e.g., "prd_0QKI8NHF").
        plan: Optional plan reference to check against.
        customer_ref_arg: Name of the kwarg that carries the customer ref.
        client: Pre-configured AsyncSolvaPay instance. If omitted, a new
                client is created per call (reads SOLVAPAY_SECRET_KEY from env).

    Example:
        sv = AsyncSolvaPay()

        @paywall.require_async(product="prd_0QKI8NHF", client=sv)
        async def run_expensive_query(*, customer_ref: str, query: str) -> dict:
            ...
    """

    def decorator(fn: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            from solvapay._async_client import AsyncSolvaPay

            customer_ref = kwargs.get(customer_ref_arg)
            if not isinstance(customer_ref, str):
                raise SolvaPayError(
                    f"@paywall.require_async expected str kwarg '{customer_ref_arg}', "
                    f"got {type(customer_ref).__name__}"
                )
            sv: AsyncSolvaPay = client if isinstance(client, AsyncSolvaPay) else AsyncSolvaPay()
            limits = await sv.check_limits(
                customer_ref=customer_ref,
                product_ref=product,
                plan_ref=plan,
            )
            if not limits.within_limits:
                checkout_url = limits.checkout_url
                if checkout_url is None:
                    try:
                        session = await sv.create_checkout_session(
                            customer_ref=customer_ref, product_ref=product, plan_ref=plan
                        )
                        checkout_url = session.checkout_url
                    except SolvaPayError:
                        pass
                raise PaywallRequired(checkout_url=checkout_url)
            return await fn(*args, **kwargs)

        return wrapper

    return decorator
