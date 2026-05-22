"""Customers resource namespace (HLD V1.3, V1.5 OR6)."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from solvapay._transport import Headers, RequestSpec
from solvapay.operations._registry import REGISTRY, _interpolate

if TYPE_CHECKING:
    from solvapay._transport import AsyncTransport, Transport

from solvapay.exceptions import SolvaPayAPIError
from solvapay.models import BalanceResponse, CreateCustomerRequest, Customer, UpdateCustomerRequest


class CustomersOperations:
    """sv.customers — customer resource operations.

    Exactly two levels deep (HLD RN shallow cap).
    sync and async methods share _build_spec (HLD OR6).
    """

    def __init__(
        self,
        *,
        sync_transport: Transport | None,
        async_transport: AsyncTransport | None,
    ) -> None:
        self._sync = sync_transport
        self._async = async_transport

    # ── sync ──

    def ensure(
        self,
        customer_ref: str,
        external_ref: str | None = None,
        *,
        email: str | None = None,
        name: str | None = None,
        idempotency_key: str | None = None,
    ) -> str:
        assert self._sync is not None
        lookup_ref = external_ref or customer_ref
        try:
            resp = self._sync.send(
                RequestSpec(
                    method="GET",
                    url="/v1/sdk/customers",
                    headers=Headers(),
                    json=None,
                    params={"externalRef": lookup_ref},
                )
            )
            ref = resp.body.get("reference") or resp.body.get("customerRef")
            if ref:
                return str(ref)
        except SolvaPayAPIError as exc:
            if exc.status_code != 404:
                raise

        req = CreateCustomerRequest(
            email=email or f"{customer_ref}-{int(time.time())}@auto-created.local",
            external_ref=lookup_ref,
            name=name,
        )
        created = self._sync.send(
            RequestSpec(
                method="POST",
                url=REGISTRY["customers.ensure"].path_template,
                headers=Headers({"Idempotency-Key": idempotency_key} if idempotency_key else None),
                json=req.model_dump(by_alias=True, exclude_none=True),
            )
        )
        ref = created.body.get("reference") or created.body.get("customerRef")
        if not ref:
            raise SolvaPayAPIError(200, f"customer create returned no reference: {created.body!r}")
        return str(ref)

    def get(
        self,
        customer_ref: str | None = None,
        *,
        external_ref: str | None = None,
        email: str | None = None,
    ) -> Customer:
        assert self._sync is not None
        if customer_ref:
            url = _interpolate(REGISTRY["customers.get"].path_template, customer_ref=customer_ref)
            resp = self._sync.send(RequestSpec(method="GET", url=url, headers=Headers(), json=None))
        elif external_ref:
            resp = self._sync.send(
                RequestSpec(
                    method="GET",
                    url="/v1/sdk/customers",
                    headers=Headers(),
                    json=None,
                    params={"externalRef": external_ref},
                )
            )
        elif email:
            resp = self._sync.send(
                RequestSpec(
                    method="GET",
                    url="/v1/sdk/customers",
                    headers=Headers(),
                    json=None,
                    params={"email": email},
                )
            )
        else:
            raise ValueError("Must provide customer_ref, external_ref, or email")
        return Customer.model_validate(resp.body)

    def update(
        self,
        customer_ref: str,
        *,
        email: str | None = None,
        name: str | None = None,
        external_ref: str | None = None,
    ) -> Customer:
        assert self._sync is not None
        req = UpdateCustomerRequest(email=email, name=name, external_ref=external_ref)
        url = _interpolate(REGISTRY["customers.update"].path_template, customer_ref=customer_ref)
        resp = self._sync.send(
            RequestSpec(
                method="PATCH",
                url=url,
                headers=Headers(),
                json=req.model_dump(by_alias=True, exclude_none=True),
            )
        )
        return Customer.model_validate(resp.body)

    def balance(self, customer_ref: str) -> BalanceResponse:
        assert self._sync is not None
        url = _interpolate(REGISTRY["customers.balance"].path_template, customer_ref=customer_ref)
        resp = self._sync.send(RequestSpec(method="GET", url=url, headers=Headers(), json=None))
        return BalanceResponse.model_validate(resp.body)

    # ── async ──

    async def aensure(
        self,
        customer_ref: str,
        external_ref: str | None = None,
        *,
        email: str | None = None,
        name: str | None = None,
        idempotency_key: str | None = None,
    ) -> str:
        assert self._async is not None
        lookup_ref = external_ref or customer_ref
        try:
            resp = await self._async.send(
                RequestSpec(
                    method="GET",
                    url="/v1/sdk/customers",
                    headers=Headers(),
                    json=None,
                    params={"externalRef": lookup_ref},
                )
            )
            ref = resp.body.get("reference") or resp.body.get("customerRef")
            if ref:
                return str(ref)
        except SolvaPayAPIError as exc:
            if exc.status_code != 404:
                raise

        req = CreateCustomerRequest(
            email=email or f"{customer_ref}-{int(time.time())}@auto-created.local",
            external_ref=lookup_ref,
            name=name,
        )
        created = await self._async.send(
            RequestSpec(
                method="POST",
                url=REGISTRY["customers.ensure"].path_template,
                headers=Headers({"Idempotency-Key": idempotency_key} if idempotency_key else None),
                json=req.model_dump(by_alias=True, exclude_none=True),
            )
        )
        ref = created.body.get("reference") or created.body.get("customerRef")
        if not ref:
            raise SolvaPayAPIError(200, f"customer create returned no reference: {created.body!r}")
        return str(ref)

    async def aget(
        self,
        customer_ref: str | None = None,
        *,
        external_ref: str | None = None,
        email: str | None = None,
    ) -> Customer:
        assert self._async is not None
        if customer_ref:
            url = _interpolate(REGISTRY["customers.get"].path_template, customer_ref=customer_ref)
            resp = await self._async.send(
                RequestSpec(method="GET", url=url, headers=Headers(), json=None)
            )
        elif external_ref:
            resp = await self._async.send(
                RequestSpec(
                    method="GET",
                    url="/v1/sdk/customers",
                    headers=Headers(),
                    json=None,
                    params={"externalRef": external_ref},
                )
            )
        elif email:
            resp = await self._async.send(
                RequestSpec(
                    method="GET",
                    url="/v1/sdk/customers",
                    headers=Headers(),
                    json=None,
                    params={"email": email},
                )
            )
        else:
            raise ValueError("Must provide customer_ref, external_ref, or email")
        return Customer.model_validate(resp.body)

    async def aupdate(
        self,
        customer_ref: str,
        *,
        email: str | None = None,
        name: str | None = None,
        external_ref: str | None = None,
    ) -> Customer:
        assert self._async is not None
        req = UpdateCustomerRequest(email=email, name=name, external_ref=external_ref)
        url = _interpolate(REGISTRY["customers.update"].path_template, customer_ref=customer_ref)
        resp = await self._async.send(
            RequestSpec(
                method="PATCH",
                url=url,
                headers=Headers(),
                json=req.model_dump(by_alias=True, exclude_none=True),
            )
        )
        return Customer.model_validate(resp.body)

    async def abalance(self, customer_ref: str) -> BalanceResponse:
        assert self._async is not None
        url = _interpolate(REGISTRY["customers.balance"].path_template, customer_ref=customer_ref)
        resp = await self._async.send(
            RequestSpec(method="GET", url=url, headers=Headers(), json=None)
        )
        return BalanceResponse.model_validate(resp.body)
