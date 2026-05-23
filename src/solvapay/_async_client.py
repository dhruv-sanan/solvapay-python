"""Async SolvaPay client. Mirrors SolvaPay sync surface 1:1.

Constructor signature identical to `SolvaPay`. All ops are `async def`.
Use `async with AsyncSolvaPay() as sv: ...` for proper teardown.
"""

from __future__ import annotations

import logging
import warnings
from typing import Any

from solvapay._config import resolve_api_key, resolve_base_url
from solvapay._http import AsyncHttpClient
from solvapay.models import (
    BalanceResponse,
    CheckoutSession,
    Customer,
    LimitResponse,
    Merchant,
    Plan,
    PlatformConfig,
    Product,
)
from solvapay.operations.checkout import CheckoutOperations
from solvapay.operations.customers import CustomersOperations
from solvapay.operations.limits import LimitsOperations
from solvapay.operations.merchant import MerchantOperations
from solvapay.operations.plans import PlansOperations
from solvapay.operations.products import ProductsOperations
from solvapay.operations.purchases import PurchasesOperations
from solvapay.operations.usage import UsageOperations


def _shim_warn(new: str) -> None:
    warnings.warn(
        f"Flat method deprecated; use {new} instead",
        DeprecationWarning,
        stacklevel=3,
    )


class AsyncSolvaPay:
    """Async SolvaPay API client.

    Resource namespaces (v0.8+):
        sv.customers.aensure / aget / aupdate / abalance
        sv.checkout.acreate_session
        sv.limits.acheck
        sv.purchases.acancel / areactivate
        sv.usage.atrack
        sv.products.alist / aget / acreate / adelete / aclone
        sv.plans.alist / acreate / aupdate / adelete
        sv.merchant.aget / aget_platform_config

    Args:
        api_key: SolvaPay secret key. Falls back to SOLVAPAY_SECRET_KEY env var.
        base_url: API base URL. Falls back to SOLVAPAY_API_BASE_URL env var,
                  then to https://api.solvapay.com.
        timeout: HTTP timeout in seconds. Default 30.

    Example:
        >>> async with AsyncSolvaPay() as sv:
        ...     session = await sv.checkout.acreate_session(
        ...         customer_ref="cus_123", product_ref="prd_0QKI8NHF"
        ...     )
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = 30.0,
        logger: logging.Logger | None = None,
        api_version: str | None = "2026-05-22",
    ) -> None:
        self._http = AsyncHttpClient(
            api_key=resolve_api_key(api_key),
            base_url=resolve_base_url(base_url),
            timeout=timeout,
            logger=logger,
            api_version=api_version,
        )
        # Eager namespace construction (HLD RN1).
        _t = self._http._transport
        self.customers = CustomersOperations(sync_transport=None, async_transport=_t)
        self.checkout = CheckoutOperations(sync_transport=None, async_transport=_t)
        self.limits = LimitsOperations(sync_transport=None, async_transport=_t)
        self.purchases = PurchasesOperations(sync_transport=None, async_transport=_t)
        self.usage = UsageOperations(sync_transport=None, async_transport=_t)
        self.products = ProductsOperations(sync_transport=None, async_transport=_t)
        self.plans = PlansOperations(sync_transport=None, async_transport=_t)
        self.merchant = MerchantOperations(sync_transport=None, async_transport=_t)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> AsyncSolvaPay:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    # ── Deprecated flat shims — removed in v2.0 ──

    async def create_checkout_session(
        self,
        *,
        customer_ref: str,
        product_ref: str,
        plan_ref: str | None = None,
        return_url: str | None = None,
        idempotency_key: str | None = None,
    ) -> CheckoutSession:
        _shim_warn("sv.checkout.acreate_session()")
        return await self.checkout.acreate_session(
            customer_ref=customer_ref,
            product_ref=product_ref,
            plan_ref=plan_ref,
            return_url=return_url,
            idempotency_key=idempotency_key,
        )

    async def ensure_customer(
        self,
        customer_ref: str,
        external_ref: str | None = None,
        *,
        email: str | None = None,
        name: str | None = None,
        idempotency_key: str | None = None,
    ) -> str:
        _shim_warn("sv.customers.aensure()")
        return await self.customers.aensure(
            customer_ref,
            external_ref,
            email=email,
            name=name,
            idempotency_key=idempotency_key,
        )

    async def get_customer(
        self,
        customer_ref: str | None = None,
        *,
        external_ref: str | None = None,
        email: str | None = None,
    ) -> Customer:
        _shim_warn("sv.customers.aget()")
        return await self.customers.aget(customer_ref, external_ref=external_ref, email=email)

    async def check_limits(
        self,
        *,
        customer_ref: str,
        product_ref: str,
        plan_ref: str | None = None,
        meter_name: str | None = None,
        usage_type: str | None = None,
    ) -> LimitResponse:
        _shim_warn("sv.limits.acheck()")
        return await self.limits.acheck(
            customer_ref=customer_ref,
            product_ref=product_ref,
            plan_ref=plan_ref,
            meter_name=meter_name,
            usage_type=usage_type,
        )

    async def track_usage(
        self,
        *,
        customer_ref: str,
        product_ref: str,
        meter_name: str,
        units: float,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        _shim_warn("sv.usage.atrack()")
        return await self.usage.atrack(
            customer_ref=customer_ref,
            product_ref=product_ref,
            meter_name=meter_name,
            units=units,
            idempotency_key=idempotency_key,
        )

    async def update_customer(
        self,
        customer_ref: str,
        *,
        email: str | None = None,
        name: str | None = None,
        external_ref: str | None = None,
    ) -> Customer:
        _shim_warn("sv.customers.aupdate()")
        return await self.customers.aupdate(
            customer_ref, email=email, name=name, external_ref=external_ref
        )

    async def get_customer_balance(self, customer_ref: str) -> BalanceResponse:
        _shim_warn("sv.customers.abalance()")
        return await self.customers.abalance(customer_ref)

    async def cancel_purchase(
        self,
        purchase_ref: str,
        *,
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        _shim_warn("sv.purchases.acancel()")
        return await self.purchases.acancel(
            purchase_ref, reason=reason, idempotency_key=idempotency_key
        )

    async def reactivate_purchase(
        self, purchase_ref: str, *, idempotency_key: str | None = None
    ) -> dict[str, Any]:
        _shim_warn("sv.purchases.areactivate()")
        return await self.purchases.areactivate(purchase_ref, idempotency_key=idempotency_key)

    async def list_products(self) -> list[Product]:
        _shim_warn("sv.products.alist()")
        return await self.products.alist()

    async def get_product(self, product_ref: str) -> Product:
        _shim_warn("sv.products.aget()")
        return await self.products.aget(product_ref)

    async def create_product(
        self, *, name: str, type: str, default_currency: str, idempotency_key: str | None = None
    ) -> Product:
        _shim_warn("sv.products.acreate()")
        return await self.products.acreate(
            name=name, type=type, default_currency=default_currency, idempotency_key=idempotency_key
        )

    async def delete_product(self, product_ref: str) -> dict[str, Any]:
        _shim_warn("sv.products.adelete()")
        return await self.products.adelete(product_ref)

    async def clone_product(
        self, product_ref: str, *, new_name: str, idempotency_key: str | None = None
    ) -> Product:
        _shim_warn("sv.products.aclone()")
        return await self.products.aclone(
            product_ref, new_name=new_name, idempotency_key=idempotency_key
        )

    async def list_plans(self, product_ref: str) -> list[Plan]:
        _shim_warn("sv.plans.alist()")
        return await self.plans.alist(product_ref)

    async def create_plan(
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
        _shim_warn("sv.plans.acreate()")
        return await self.plans.acreate(
            product_ref,
            name=name,
            type=type,
            price=price,
            currency=currency,
            interval=interval,
            idempotency_key=idempotency_key,
        )

    async def update_plan(
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
        _shim_warn("sv.plans.aupdate()")
        return await self.plans.aupdate(
            product_ref,
            plan_ref,
            name=name,
            type=type,
            price=price,
            currency=currency,
            interval=interval,
        )

    async def delete_plan(self, product_ref: str, plan_ref: str) -> dict[str, Any]:
        _shim_warn("sv.plans.adelete()")
        return await self.plans.adelete(product_ref, plan_ref)

    async def get_merchant(self) -> Merchant:
        _shim_warn("sv.merchant.aget()")
        return await self.merchant.aget()

    async def get_platform_config(self) -> PlatformConfig:
        _shim_warn("sv.merchant.aget_platform_config()")
        return await self.merchant.aget_platform_config()
