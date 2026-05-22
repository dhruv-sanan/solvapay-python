"""Purchases resource namespace."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from solvapay._transport import Headers, RequestSpec
from solvapay.models import CancelPurchaseRequest
from solvapay.operations._registry import REGISTRY, _interpolate

if TYPE_CHECKING:
    from solvapay._transport import AsyncTransport, Transport


class PurchasesOperations:
    def __init__(
        self,
        *,
        sync_transport: Transport | None,
        async_transport: AsyncTransport | None,
    ) -> None:
        self._sync = sync_transport
        self._async = async_transport

    def cancel(
        self,
        purchase_ref: str,
        *,
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        assert self._sync is not None
        req = CancelPurchaseRequest(reason=reason)
        url = _interpolate(REGISTRY["purchases.cancel"].path_template, purchase_ref=purchase_ref)
        resp = self._sync.send(
            RequestSpec(
                method="POST",
                url=url,
                headers=Headers({"Idempotency-Key": idempotency_key} if idempotency_key else None),
                json=req.model_dump(by_alias=True, exclude_none=True),
            )
        )
        return resp.body

    def reactivate(
        self,
        purchase_ref: str,
        *,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        assert self._sync is not None
        url = _interpolate(
            REGISTRY["purchases.reactivate"].path_template, purchase_ref=purchase_ref
        )
        resp = self._sync.send(
            RequestSpec(
                method="POST",
                url=url,
                headers=Headers({"Idempotency-Key": idempotency_key} if idempotency_key else None),
                json=None,
            )
        )
        return resp.body

    async def acancel(
        self,
        purchase_ref: str,
        *,
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        assert self._async is not None
        req = CancelPurchaseRequest(reason=reason)
        url = _interpolate(REGISTRY["purchases.cancel"].path_template, purchase_ref=purchase_ref)
        resp = await self._async.send(
            RequestSpec(
                method="POST",
                url=url,
                headers=Headers({"Idempotency-Key": idempotency_key} if idempotency_key else None),
                json=req.model_dump(by_alias=True, exclude_none=True),
            )
        )
        return resp.body

    async def areactivate(
        self,
        purchase_ref: str,
        *,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        assert self._async is not None
        url = _interpolate(
            REGISTRY["purchases.reactivate"].path_template, purchase_ref=purchase_ref
        )
        resp = await self._async.send(
            RequestSpec(
                method="POST",
                url=url,
                headers=Headers({"Idempotency-Key": idempotency_key} if idempotency_key else None),
                json=None,
            )
        )
        return resp.body
