"""Products resource namespace."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from solvapay._transport import Headers, RequestSpec
from solvapay.models import CloneProductRequest, CreateProductRequest, Product
from solvapay.operations._registry import REGISTRY, _interpolate

if TYPE_CHECKING:
    from solvapay._transport import AsyncTransport, Transport


class ProductsOperations:
    def __init__(
        self,
        *,
        sync_transport: Transport | None,
        async_transport: AsyncTransport | None,
    ) -> None:
        self._sync = sync_transport
        self._async = async_transport

    def list(self) -> list[Product]:
        assert self._sync is not None
        resp = self._sync.send(
            RequestSpec(
                method="GET",
                url=REGISTRY["products.list"].path_template,
                headers=Headers(),
                json=None,
            )
        )
        items = resp.body if isinstance(resp.body, list) else resp.body.get("products", [])
        return [Product.model_validate(p) for p in items]

    def get(self, product_ref: str) -> Product:
        assert self._sync is not None
        url = _interpolate(REGISTRY["products.get"].path_template, product_ref=product_ref)
        resp = self._sync.send(RequestSpec(method="GET", url=url, headers=Headers(), json=None))
        return Product.model_validate(resp.body)

    def create(
        self, *, name: str, type: str, default_currency: str, idempotency_key: str | None = None
    ) -> Product:
        assert self._sync is not None
        req = CreateProductRequest(name=name, type=type, default_currency=default_currency)
        resp = self._sync.send(
            RequestSpec(
                method="POST",
                url=REGISTRY["products.create"].path_template,
                headers=Headers({"Idempotency-Key": idempotency_key} if idempotency_key else None),
                json=req.model_dump(by_alias=True, exclude_none=True),
            )
        )
        return Product.model_validate(resp.body)

    def delete(self, product_ref: str) -> dict[str, Any]:
        assert self._sync is not None
        url = _interpolate(REGISTRY["products.delete"].path_template, product_ref=product_ref)
        resp = self._sync.send(RequestSpec(method="DELETE", url=url, headers=Headers(), json=None))
        return resp.body

    def clone(
        self, product_ref: str, *, new_name: str, idempotency_key: str | None = None
    ) -> Product:
        assert self._sync is not None
        req = CloneProductRequest(new_name=new_name)
        url = _interpolate(REGISTRY["products.clone"].path_template, product_ref=product_ref)
        resp = self._sync.send(
            RequestSpec(
                method="POST",
                url=url,
                headers=Headers({"Idempotency-Key": idempotency_key} if idempotency_key else None),
                json=req.model_dump(by_alias=True, exclude_none=True),
            )
        )
        return Product.model_validate(resp.body)

    # ── async ──

    async def alist(self) -> list[Product]:
        assert self._async is not None
        resp = await self._async.send(
            RequestSpec(
                method="GET",
                url=REGISTRY["products.list"].path_template,
                headers=Headers(),
                json=None,
            )
        )
        items = resp.body if isinstance(resp.body, list) else resp.body.get("products", [])
        return [Product.model_validate(p) for p in items]

    async def aget(self, product_ref: str) -> Product:
        assert self._async is not None
        url = _interpolate(REGISTRY["products.get"].path_template, product_ref=product_ref)
        resp = await self._async.send(
            RequestSpec(method="GET", url=url, headers=Headers(), json=None)
        )
        return Product.model_validate(resp.body)

    async def acreate(
        self, *, name: str, type: str, default_currency: str, idempotency_key: str | None = None
    ) -> Product:
        assert self._async is not None
        req = CreateProductRequest(name=name, type=type, default_currency=default_currency)
        resp = await self._async.send(
            RequestSpec(
                method="POST",
                url=REGISTRY["products.create"].path_template,
                headers=Headers({"Idempotency-Key": idempotency_key} if idempotency_key else None),
                json=req.model_dump(by_alias=True, exclude_none=True),
            )
        )
        return Product.model_validate(resp.body)

    async def adelete(self, product_ref: str) -> dict[str, Any]:
        assert self._async is not None
        url = _interpolate(REGISTRY["products.delete"].path_template, product_ref=product_ref)
        resp = await self._async.send(
            RequestSpec(method="DELETE", url=url, headers=Headers(), json=None)
        )
        return resp.body

    async def aclone(
        self, product_ref: str, *, new_name: str, idempotency_key: str | None = None
    ) -> Product:
        assert self._async is not None
        req = CloneProductRequest(new_name=new_name)
        url = _interpolate(REGISTRY["products.clone"].path_template, product_ref=product_ref)
        resp = await self._async.send(
            RequestSpec(
                method="POST",
                url=url,
                headers=Headers({"Idempotency-Key": idempotency_key} if idempotency_key else None),
                json=req.model_dump(by_alias=True, exclude_none=True),
            )
        )
        return Product.model_validate(resp.body)
