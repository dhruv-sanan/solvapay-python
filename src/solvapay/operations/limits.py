"""Limits resource namespace."""

from __future__ import annotations

from typing import TYPE_CHECKING

from solvapay._transport import Headers, RequestSpec
from solvapay.models import CheckLimitsRequest, LimitResponse
from solvapay.operations._registry import REGISTRY

if TYPE_CHECKING:
    from solvapay._transport import AsyncTransport, Transport


class LimitsOperations:
    def __init__(
        self,
        *,
        sync_transport: Transport | None,
        async_transport: AsyncTransport | None,
    ) -> None:
        self._sync = sync_transport
        self._async = async_transport

    def check(
        self,
        *,
        customer_ref: str,
        product_ref: str,
        plan_ref: str | None = None,
        meter_name: str | None = None,
        usage_type: str | None = None,
    ) -> LimitResponse:
        assert self._sync is not None
        req = CheckLimitsRequest(
            customer_ref=customer_ref,
            product_ref=product_ref,
            plan_ref=plan_ref,
            meter_name=meter_name,
            usage_type=usage_type,
        )
        resp = self._sync.send(
            RequestSpec(
                method="POST",
                url=REGISTRY["limits.check"].path_template,
                headers=Headers(),
                json=req.model_dump(by_alias=True, exclude_none=True),
            )
        )
        return LimitResponse.model_validate(resp.body)

    async def acheck(
        self,
        *,
        customer_ref: str,
        product_ref: str,
        plan_ref: str | None = None,
        meter_name: str | None = None,
        usage_type: str | None = None,
    ) -> LimitResponse:
        assert self._async is not None
        req = CheckLimitsRequest(
            customer_ref=customer_ref,
            product_ref=product_ref,
            plan_ref=plan_ref,
            meter_name=meter_name,
            usage_type=usage_type,
        )
        resp = await self._async.send(
            RequestSpec(
                method="POST",
                url=REGISTRY["limits.check"].path_template,
                headers=Headers(),
                json=req.model_dump(by_alias=True, exclude_none=True),
            )
        )
        return LimitResponse.model_validate(resp.body)
