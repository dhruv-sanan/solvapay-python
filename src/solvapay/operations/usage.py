"""Usage resource namespace."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from solvapay._transport import Headers, RequestSpec
from solvapay.models import TrackUsageRequest
from solvapay.operations._registry import REGISTRY

if TYPE_CHECKING:
    from solvapay._transport import AsyncTransport, Transport


class UsageOperations:
    def __init__(
        self,
        *,
        sync_transport: Transport | None,
        async_transport: AsyncTransport | None,
    ) -> None:
        self._sync = sync_transport
        self._async = async_transport

    def track(
        self,
        *,
        customer_ref: str,
        product_ref: str,
        meter_name: str,
        units: float,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        assert self._sync is not None
        req = TrackUsageRequest(
            customer_ref=customer_ref,
            product_ref=product_ref,
            meter_name=meter_name,
            units=units,
        )
        resp = self._sync.send(
            RequestSpec(
                method="POST",
                url=REGISTRY["usage.track"].path_template,
                headers=Headers({"Idempotency-Key": idempotency_key} if idempotency_key else None),
                json=req.model_dump(by_alias=True, exclude_none=True),
            )
        )
        return resp.body

    async def atrack(
        self,
        *,
        customer_ref: str,
        product_ref: str,
        meter_name: str,
        units: float,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        assert self._async is not None
        req = TrackUsageRequest(
            customer_ref=customer_ref,
            product_ref=product_ref,
            meter_name=meter_name,
            units=units,
        )
        resp = await self._async.send(
            RequestSpec(
                method="POST",
                url=REGISTRY["usage.track"].path_template,
                headers=Headers({"Idempotency-Key": idempotency_key} if idempotency_key else None),
                json=req.model_dump(by_alias=True, exclude_none=True),
            )
        )
        return resp.body
