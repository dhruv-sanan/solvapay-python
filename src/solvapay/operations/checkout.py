"""Checkout resource namespace."""

from __future__ import annotations

from typing import TYPE_CHECKING

from solvapay._transport import Headers, RequestSpec
from solvapay.models import CheckoutSession, CheckoutSessionRequest
from solvapay.operations._registry import REGISTRY

if TYPE_CHECKING:
    from solvapay._transport import AsyncTransport, Transport


class CheckoutOperations:
    def __init__(
        self,
        *,
        sync_transport: Transport | None,
        async_transport: AsyncTransport | None,
    ) -> None:
        self._sync = sync_transport
        self._async = async_transport

    def create_session(
        self,
        *,
        customer_ref: str,
        product_ref: str,
        plan_ref: str | None = None,
        return_url: str | None = None,
        idempotency_key: str | None = None,
    ) -> CheckoutSession:
        assert self._sync is not None
        req = CheckoutSessionRequest(
            customer_ref=customer_ref,
            product_ref=product_ref,
            plan_ref=plan_ref,
            return_url=return_url,
        )
        resp = self._sync.send(
            RequestSpec(
                method="POST",
                url=REGISTRY["checkout.create_session"].path_template,
                headers=Headers({"Idempotency-Key": idempotency_key} if idempotency_key else None),
                json=req.model_dump(by_alias=True, exclude_none=True),
            )
        )
        return CheckoutSession.model_validate(resp.body)

    async def acreate_session(
        self,
        *,
        customer_ref: str,
        product_ref: str,
        plan_ref: str | None = None,
        return_url: str | None = None,
        idempotency_key: str | None = None,
    ) -> CheckoutSession:
        assert self._async is not None
        req = CheckoutSessionRequest(
            customer_ref=customer_ref,
            product_ref=product_ref,
            plan_ref=plan_ref,
            return_url=return_url,
        )
        resp = await self._async.send(
            RequestSpec(
                method="POST",
                url=REGISTRY["checkout.create_session"].path_template,
                headers=Headers({"Idempotency-Key": idempotency_key} if idempotency_key else None),
                json=req.model_dump(by_alias=True, exclude_none=True),
            )
        )
        return CheckoutSession.model_validate(resp.body)
