"""Paywall + AsyncPaywall classes (HLD V1.6 PW1 lock: two classes, not one)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from solvapay.exceptions import APIError, SolvaPayError

if TYPE_CHECKING:
    from solvapay._async_client import AsyncSolvaPay
    from solvapay.client import SolvaPay
    from solvapay.paywall.resolvers import KwargsResolver


class PaywallRequired(SolvaPayError):
    """Raised when a customer has exceeded their limits.

    checkout_mint_error is set when the paywall tried to mint a checkout URL
    automatically but the create_checkout_session call failed (HLD V1.6 PW3).
    """

    def __init__(
        self,
        checkout_url: str | None,
        message: str = "Paywall: limit exceeded",
        *,
        checkout_mint_error: APIError | None = None,
    ) -> None:
        self.checkout_url = checkout_url
        self.checkout_mint_error: APIError | None = checkout_mint_error  # HLD PW3
        super().__init__(message)


class Paywall:
    """Synchronous paywall gate. Requires a SolvaPay (sync) client (HLD V1.6 PW1)."""

    def __init__(
        self,
        *,
        client: SolvaPay,
        product: str,
        plan: str | None = None,
        customer_ref_resolver: KwargsResolver | None = None,
        customer_ref_arg: str = "customer_ref",
    ) -> None:
        from solvapay._async_client import AsyncSolvaPay as _AsyncSolvaPay

        if isinstance(client, _AsyncSolvaPay):
            raise TypeError(
                "Paywall received an AsyncSolvaPay client. Use AsyncPaywall for async clients."
            )
        self._client = client
        self._product = product
        self._plan = plan
        self._resolver = customer_ref_resolver
        self._customer_ref_arg = customer_ref_arg

    def gate(self, *args: Any, **kwargs: Any) -> None:
        """Check limits. Raises PaywallRequired if blocked, returns None if OK."""
        if self._resolver is not None:
            customer_ref = self._resolver.resolve(*args, **kwargs)
        else:
            customer_ref = kwargs.get(self._customer_ref_arg)
            if not isinstance(customer_ref, str):
                raise SolvaPayError(
                    f"Paywall.gate: expected str kwarg '{self._customer_ref_arg}', "
                    f"got {type(customer_ref).__name__}"
                )

        limits = self._client.limits.check(
            customer_ref=customer_ref,
            product_ref=self._product,
            plan_ref=self._plan,
        )
        if not limits.within_limits:
            checkout_url = limits.checkout_url
            mint_error: APIError | None = None
            if checkout_url is None:
                try:
                    session = self._client.checkout.create_session(
                        customer_ref=customer_ref,
                        product_ref=self._product,
                        plan_ref=self._plan,
                    )
                    checkout_url = session.checkout_url
                except APIError as exc:
                    mint_error = exc
                except SolvaPayError:
                    pass
            raise PaywallRequired(checkout_url=checkout_url, checkout_mint_error=mint_error)


class AsyncPaywall:
    """Async paywall gate. Requires an AsyncSolvaPay client (HLD V1.6 PW1)."""

    def __init__(
        self,
        *,
        client: AsyncSolvaPay,
        product: str,
        plan: str | None = None,
        customer_ref_resolver: KwargsResolver | None = None,
        customer_ref_arg: str = "customer_ref",
    ) -> None:
        from solvapay._async_client import AsyncSolvaPay as _AsyncSolvaPay

        if not isinstance(client, _AsyncSolvaPay):
            raise TypeError(
                f"AsyncPaywall requires an AsyncSolvaPay client, got {type(client).__name__}. "
                "Use Paywall for sync clients."
            )
        self._client = client
        self._product = product
        self._plan = plan
        self._resolver = customer_ref_resolver
        self._customer_ref_arg = customer_ref_arg

    async def gate(self, *args: Any, **kwargs: Any) -> None:
        """Async limit check. Raises PaywallRequired if blocked."""
        if self._resolver is not None:
            customer_ref = self._resolver.resolve(*args, **kwargs)
        else:
            customer_ref = kwargs.get(self._customer_ref_arg)
            if not isinstance(customer_ref, str):
                raise SolvaPayError(
                    f"AsyncPaywall.gate: expected str kwarg '{self._customer_ref_arg}', "
                    f"got {type(customer_ref).__name__}"
                )

        limits = await self._client.limits.acheck(
            customer_ref=customer_ref,
            product_ref=self._product,
            plan_ref=self._plan,
        )
        if not limits.within_limits:
            checkout_url = limits.checkout_url
            mint_error: APIError | None = None
            if checkout_url is None:
                try:
                    session = await self._client.checkout.acreate_session(
                        customer_ref=customer_ref,
                        product_ref=self._product,
                        plan_ref=self._plan,
                    )
                    checkout_url = session.checkout_url
                except APIError as exc:
                    mint_error = exc
                except SolvaPayError:
                    pass
            raise PaywallRequired(checkout_url=checkout_url, checkout_mint_error=mint_error)
