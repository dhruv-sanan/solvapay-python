"""Plans resource namespace."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from solvapay._transport import Headers, RequestSpec
from solvapay.models import CreatePlanRequest, Plan, UpdatePlanRequest
from solvapay.operations._registry import REGISTRY, _interpolate

if TYPE_CHECKING:
    from solvapay._transport import AsyncTransport, Transport


class PlansOperations:
    def __init__(
        self,
        *,
        sync_transport: Transport | None,
        async_transport: AsyncTransport | None,
    ) -> None:
        self._sync = sync_transport
        self._async = async_transport

    def list(self, product_ref: str) -> list[Plan]:
        assert self._sync is not None
        url = _interpolate(REGISTRY["plans.list"].path_template, product_ref=product_ref)
        resp = self._sync.send(RequestSpec(method="GET", url=url, headers=Headers(), json=None))
        items = resp.body if isinstance(resp.body, list) else resp.body.get("plans", [])
        return [Plan.model_validate(p) for p in items]

    def create(
        self,
        product_ref: str,
        *,
        name: str,
        type: str,
        price: float | None = None,
        currency: str | None = None,
        interval: str | None = None,
        idempotency_key: str | None = None,
    ) -> Plan:
        assert self._sync is not None
        req = CreatePlanRequest(
            name=name, type=type, price=price, currency=currency, interval=interval
        )
        url = _interpolate(REGISTRY["plans.create"].path_template, product_ref=product_ref)
        resp = self._sync.send(
            RequestSpec(
                method="POST",
                url=url,
                headers=Headers({"Idempotency-Key": idempotency_key} if idempotency_key else None),
                json=req.model_dump(by_alias=True, exclude_none=True),
            )
        )
        return Plan.model_validate(resp.body)

    def update(
        self,
        product_ref: str,
        plan_ref: str,
        *,
        name: str | None = None,
        type: str | None = None,
        price: float | None = None,
        currency: str | None = None,
        interval: str | None = None,
    ) -> Plan:
        assert self._sync is not None
        req = UpdatePlanRequest(
            name=name, type=type, price=price, currency=currency, interval=interval
        )
        url = _interpolate(
            REGISTRY["plans.update"].path_template, product_ref=product_ref, plan_ref=plan_ref
        )
        resp = self._sync.send(
            RequestSpec(
                method="PUT",
                url=url,
                headers=Headers(),
                json=req.model_dump(by_alias=True, exclude_none=True),
            )
        )
        return Plan.model_validate(resp.body)

    def delete(self, product_ref: str, plan_ref: str) -> dict[str, Any]:
        assert self._sync is not None
        url = _interpolate(
            REGISTRY["plans.delete"].path_template, product_ref=product_ref, plan_ref=plan_ref
        )
        resp = self._sync.send(RequestSpec(method="DELETE", url=url, headers=Headers(), json=None))
        return resp.body

    # ── async ──

    async def alist(self, product_ref: str) -> list[Plan]:
        assert self._async is not None
        url = _interpolate(REGISTRY["plans.list"].path_template, product_ref=product_ref)
        resp = await self._async.send(
            RequestSpec(method="GET", url=url, headers=Headers(), json=None)
        )
        items = resp.body if isinstance(resp.body, list) else resp.body.get("plans", [])
        return [Plan.model_validate(p) for p in items]

    async def acreate(
        self,
        product_ref: str,
        *,
        name: str,
        type: str,
        price: float | None = None,
        currency: str | None = None,
        interval: str | None = None,
        idempotency_key: str | None = None,
    ) -> Plan:
        assert self._async is not None
        req = CreatePlanRequest(
            name=name, type=type, price=price, currency=currency, interval=interval
        )
        url = _interpolate(REGISTRY["plans.create"].path_template, product_ref=product_ref)
        resp = await self._async.send(
            RequestSpec(
                method="POST",
                url=url,
                headers=Headers({"Idempotency-Key": idempotency_key} if idempotency_key else None),
                json=req.model_dump(by_alias=True, exclude_none=True),
            )
        )
        return Plan.model_validate(resp.body)

    async def aupdate(
        self,
        product_ref: str,
        plan_ref: str,
        *,
        name: str | None = None,
        type: str | None = None,
        price: float | None = None,
        currency: str | None = None,
        interval: str | None = None,
    ) -> Plan:
        assert self._async is not None
        req = UpdatePlanRequest(
            name=name, type=type, price=price, currency=currency, interval=interval
        )
        url = _interpolate(
            REGISTRY["plans.update"].path_template, product_ref=product_ref, plan_ref=plan_ref
        )
        resp = await self._async.send(
            RequestSpec(
                method="PUT",
                url=url,
                headers=Headers(),
                json=req.model_dump(by_alias=True, exclude_none=True),
            )
        )
        return Plan.model_validate(resp.body)

    async def adelete(self, product_ref: str, plan_ref: str) -> dict[str, Any]:
        assert self._async is not None
        url = _interpolate(
            REGISTRY["plans.delete"].path_template, product_ref=product_ref, plan_ref=plan_ref
        )
        resp = await self._async.send(
            RequestSpec(method="DELETE", url=url, headers=Headers(), json=None)
        )
        return resp.body
