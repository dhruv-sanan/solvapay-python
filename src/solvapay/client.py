"""Public SolvaPay client. Synchronous; mirrors @solvapay/core surface."""

from __future__ import annotations

import logging
import warnings
from typing import Any

from solvapay._config import resolve_api_key, resolve_base_url
from solvapay._http import HttpClient
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


class SolvaPay:
    """Synchronous SolvaPay API client.

    Resource namespaces (v0.8+):
        sv.customers.ensure / get / update / balance
        sv.checkout.create_session
        sv.limits.check
        sv.purchases.cancel / reactivate
        sv.usage.track
        sv.products.list / get / create / delete / clone
        sv.plans.list / create / update / delete
        sv.merchant.get / get_platform_config

    Flat methods (deprecated, removed in 2.0):
        sv.ensure_customer, sv.create_checkout_session, etc.

    Args:
        api_key: SolvaPay secret key. Falls back to SOLVAPAY_SECRET_KEY env var.
        base_url: API base URL. Falls back to SOLVAPAY_API_BASE_URL env var,
                  then to https://api.solvapay.com.
        timeout: HTTP timeout in seconds. Default 30.

    Example:
        >>> from solvapay import SolvaPay
        >>> sv = SolvaPay()
        >>> customer_ref = sv.customers.ensure("user_123")
        >>> session = sv.checkout.create_session(
        ...     customer_ref=customer_ref, product_ref="prd_0QKI8NHF"
        ... )
        >>> print(session.checkout_url)
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
        self._http = HttpClient(
            api_key=resolve_api_key(api_key),
            base_url=resolve_base_url(base_url),
            timeout=timeout,
            logger=logger,
            api_version=api_version,
        )
        # Eager namespace construction (HLD RN1).
        # Reuses the underlying HttpxTransport from _http for zero double-init.
        _t = self._http._transport
        self.customers = CustomersOperations(sync_transport=_t, async_transport=None)
        self.checkout = CheckoutOperations(sync_transport=_t, async_transport=None)
        self.limits = LimitsOperations(sync_transport=_t, async_transport=None)
        self.purchases = PurchasesOperations(sync_transport=_t, async_transport=None)
        self.usage = UsageOperations(sync_transport=_t, async_transport=None)
        self.products = ProductsOperations(sync_transport=_t, async_transport=None)
        self.plans = PlansOperations(sync_transport=_t, async_transport=None)
        self.merchant = MerchantOperations(sync_transport=_t, async_transport=None)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> SolvaPay:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    # ── Deprecated flat shims — removed in v2.0 ──

    def create_checkout_session(
        self,
        *,
        customer_ref: str,
        product_ref: str,
        plan_ref: str | None = None,
        return_url: str | None = None,
        idempotency_key: str | None = None,
    ) -> CheckoutSession:
        _shim_warn("sv.checkout.create_session()")
        return self.checkout.create_session(
            customer_ref=customer_ref,
            product_ref=product_ref,
            plan_ref=plan_ref,
            return_url=return_url,
            idempotency_key=idempotency_key,
        )

    def ensure_customer(
        self,
        customer_ref: str,
        external_ref: str | None = None,
        *,
        email: str | None = None,
        name: str | None = None,
        idempotency_key: str | None = None,
    ) -> str:
        _shim_warn("sv.customers.ensure()")
        return self.customers.ensure(
            customer_ref,
            external_ref,
            email=email,
            name=name,
            idempotency_key=idempotency_key,
        )

    def get_customer(
        self,
        customer_ref: str | None = None,
        *,
        external_ref: str | None = None,
        email: str | None = None,
    ) -> Customer:
        _shim_warn("sv.customers.get()")
        return self.customers.get(customer_ref, external_ref=external_ref, email=email)

    def check_limits(
        self,
        *,
        customer_ref: str,
        product_ref: str,
        plan_ref: str | None = None,
        meter_name: str | None = None,
        usage_type: str | None = None,
    ) -> LimitResponse:
        _shim_warn("sv.limits.check()")
        return self.limits.check(
            customer_ref=customer_ref,
            product_ref=product_ref,
            plan_ref=plan_ref,
            meter_name=meter_name,
            usage_type=usage_type,
        )

    def track_usage(
        self,
        *,
        customer_ref: str,
        product_ref: str,
        meter_name: str,
        units: float,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        _shim_warn("sv.usage.track()")
        return self.usage.track(
            customer_ref=customer_ref,
            product_ref=product_ref,
            meter_name=meter_name,
            units=units,
            idempotency_key=idempotency_key,
        )

    def update_customer(
        self,
        customer_ref: str,
        *,
        email: str | None = None,
        name: str | None = None,
        external_ref: str | None = None,
    ) -> Customer:
        _shim_warn("sv.customers.update()")
        return self.customers.update(
            customer_ref, email=email, name=name, external_ref=external_ref
        )

    def get_customer_balance(self, customer_ref: str) -> BalanceResponse:
        _shim_warn("sv.customers.balance()")
        return self.customers.balance(customer_ref)

    def cancel_purchase(
        self, purchase_ref: str, *, reason: str | None = None, idempotency_key: str | None = None
    ) -> dict[str, Any]:
        _shim_warn("sv.purchases.cancel()")
        return self.purchases.cancel(purchase_ref, reason=reason, idempotency_key=idempotency_key)

    def reactivate_purchase(
        self, purchase_ref: str, *, idempotency_key: str | None = None
    ) -> dict[str, Any]:
        _shim_warn("sv.purchases.reactivate()")
        return self.purchases.reactivate(purchase_ref, idempotency_key=idempotency_key)

    def list_products(self) -> list[Product]:
        _shim_warn("sv.products.list()")
        return self.products.list()

    def get_product(self, product_ref: str) -> Product:
        _shim_warn("sv.products.get()")
        return self.products.get(product_ref)

    def create_product(
        self, *, name: str, type: str, default_currency: str, idempotency_key: str | None = None
    ) -> Product:
        _shim_warn("sv.products.create()")
        return self.products.create(
            name=name, type=type, default_currency=default_currency, idempotency_key=idempotency_key
        )

    def delete_product(self, product_ref: str) -> dict[str, Any]:
        _shim_warn("sv.products.delete()")
        return self.products.delete(product_ref)

    def clone_product(
        self, product_ref: str, *, new_name: str, idempotency_key: str | None = None
    ) -> Product:
        _shim_warn("sv.products.clone()")
        return self.products.clone(product_ref, new_name=new_name, idempotency_key=idempotency_key)

    def list_plans(self, product_ref: str) -> list[Plan]:
        _shim_warn("sv.plans.list()")
        return self.plans.list(product_ref)

    def create_plan(
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
        _shim_warn("sv.plans.create()")
        return self.plans.create(
            product_ref,
            name=name,
            type=type,
            price=price,
            currency=currency,
            interval=interval,
            idempotency_key=idempotency_key,
        )

    def update_plan(
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
        _shim_warn("sv.plans.update()")
        return self.plans.update(
            product_ref,
            plan_ref,
            name=name,
            type=type,
            price=price,
            currency=currency,
            interval=interval,
        )

    def delete_plan(self, product_ref: str, plan_ref: str) -> dict[str, Any]:
        _shim_warn("sv.plans.delete()")
        return self.plans.delete(product_ref, plan_ref)

    def get_merchant(self) -> Merchant:
        _shim_warn("sv.merchant.get()")
        return self.merchant.get()

    def get_platform_config(self) -> PlatformConfig:
        _shim_warn("sv.merchant.get_platform_config()")
        return self.merchant.get_platform_config()
