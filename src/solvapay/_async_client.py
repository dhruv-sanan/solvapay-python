"""Async SolvaPay client. Mirrors SolvaPay sync surface 1:1.

Constructor signature identical to `SolvaPay`. All ops are `async def`.
Use `async with AsyncSolvaPay() as sv: ...` for proper teardown.
"""

from __future__ import annotations

import time
from typing import Any

from solvapay._config import resolve_api_key, resolve_base_url
from solvapay._http import AsyncHttpClient, _RequestSpec
from solvapay.exceptions import SolvaPayAPIError
from solvapay.models import (
    BalanceResponse,
    CancelPurchaseRequest,
    CheckLimitsRequest,
    CheckoutSession,
    CheckoutSessionRequest,
    CloneProductRequest,
    CreateCustomerRequest,
    CreatePlanRequest,
    CreateProductRequest,
    Customer,
    LimitResponse,
    Merchant,
    Plan,
    PlatformConfig,
    Product,
    TrackUsageRequest,
    UpdateCustomerRequest,
    UpdatePlanRequest,
)


class AsyncSolvaPay:
    """Async SolvaPay API client.

    Args:
        api_key: SolvaPay secret key. Falls back to SOLVAPAY_SECRET_KEY env var.
        base_url: API base URL. Falls back to SOLVAPAY_API_BASE_URL env var,
                  then to https://api.solvapay.com.
        timeout: HTTP timeout in seconds. Default 30.

    Example:
        >>> async with AsyncSolvaPay() as sv:
        ...     session = await sv.create_checkout_session(
        ...         customer_ref="cus_123", product_ref="prd_0QKI8NHF"
        ...     )
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._http = AsyncHttpClient(
            api_key=resolve_api_key(api_key),
            base_url=resolve_base_url(base_url),
            timeout=timeout,
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> AsyncSolvaPay:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def create_checkout_session(
        self,
        *,
        customer_ref: str,
        product_ref: str,
        plan_ref: str | None = None,
        return_url: str | None = None,
        idempotency_key: str | None = None,
    ) -> CheckoutSession:
        req = CheckoutSessionRequest(
            customer_ref=customer_ref,
            product_ref=product_ref,
            plan_ref=plan_ref,
            return_url=return_url,
        )
        data = await self._http.send(
            _RequestSpec(
                "POST",
                "/v1/sdk/checkout-sessions",
                json=req.model_dump(by_alias=True, exclude_none=True),
                idempotency_key=idempotency_key,
            )
        )
        return CheckoutSession.model_validate(data)

    async def ensure_customer(
        self,
        customer_ref: str,
        external_ref: str | None = None,
        *,
        email: str | None = None,
        name: str | None = None,
        idempotency_key: str | None = None,
    ) -> str:
        lookup_ref = external_ref or customer_ref
        try:
            existing = await self._http.send(
                _RequestSpec("GET", "/v1/sdk/customers", params={"externalRef": lookup_ref})
            )
            ref = existing.get("reference") or existing.get("customerRef")
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
        created = await self._http.send(
            _RequestSpec(
                "POST",
                "/v1/sdk/customers",
                json=req.model_dump(by_alias=True, exclude_none=True),
                idempotency_key=idempotency_key,
            )
        )
        ref = created.get("reference") or created.get("customerRef")
        if not ref:
            raise SolvaPayAPIError(200, f"customer create returned no reference: {created!r}")
        return str(ref)

    async def get_customer(
        self,
        customer_ref: str | None = None,
        *,
        external_ref: str | None = None,
        email: str | None = None,
    ) -> Customer:
        if customer_ref:
            data = await self._http.send(_RequestSpec("GET", f"/v1/sdk/customers/{customer_ref}"))
        elif external_ref:
            data = await self._http.send(
                _RequestSpec("GET", "/v1/sdk/customers", params={"externalRef": external_ref})
            )
        elif email:
            data = await self._http.send(
                _RequestSpec("GET", "/v1/sdk/customers", params={"email": email})
            )
        else:
            raise ValueError("Must provide customer_ref, external_ref, or email")
        return Customer.model_validate(data)

    async def check_limits(
        self,
        *,
        customer_ref: str,
        product_ref: str,
        plan_ref: str | None = None,
        meter_name: str | None = None,
        usage_type: str | None = None,
    ) -> LimitResponse:
        req = CheckLimitsRequest(
            customer_ref=customer_ref,
            product_ref=product_ref,
            plan_ref=plan_ref,
            meter_name=meter_name,
            usage_type=usage_type,
        )
        data = await self._http.send(
            _RequestSpec(
                "POST", "/v1/sdk/limits", json=req.model_dump(by_alias=True, exclude_none=True)
            )
        )
        return LimitResponse.model_validate(data)

    async def track_usage(
        self,
        *,
        customer_ref: str,
        product_ref: str,
        meter_name: str,
        units: float,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Record usage against a meter. Maps to POST /v1/sdk/usages."""
        req = TrackUsageRequest(
            customer_ref=customer_ref,
            product_ref=product_ref,
            meter_name=meter_name,
            units=units,
        )
        return await self._http.send(
            _RequestSpec(
                "POST",
                "/v1/sdk/usages",
                json=req.model_dump(by_alias=True, exclude_none=True),
                idempotency_key=idempotency_key,
            )
        )

    async def update_customer(
        self,
        customer_ref: str,
        *,
        email: str | None = None,
        name: str | None = None,
        external_ref: str | None = None,
    ) -> Customer:
        """Update customer fields. Maps to PATCH /v1/sdk/customers/{ref}."""
        req = UpdateCustomerRequest(email=email, name=name, external_ref=external_ref)
        data = await self._http.send(
            _RequestSpec(
                "PATCH",
                f"/v1/sdk/customers/{customer_ref}",
                json=req.model_dump(by_alias=True, exclude_none=True),
            )
        )
        return Customer.model_validate(data)

    async def get_customer_balance(self, customer_ref: str) -> BalanceResponse:
        """Get credit balance for a customer. Maps to GET /v1/sdk/customers/{ref}/balance."""
        data = await self._http.send(
            _RequestSpec("GET", f"/v1/sdk/customers/{customer_ref}/balance")
        )
        return BalanceResponse.model_validate(data)

    async def cancel_purchase(
        self,
        purchase_ref: str,
        *,
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Cancel a purchase. Maps to POST /v1/sdk/purchases/{ref}/cancel."""
        req = CancelPurchaseRequest(reason=reason)
        return await self._http.send(
            _RequestSpec(
                "POST",
                f"/v1/sdk/purchases/{purchase_ref}/cancel",
                json=req.model_dump(by_alias=True, exclude_none=True),
                idempotency_key=idempotency_key,
            )
        )

    async def reactivate_purchase(
        self, purchase_ref: str, *, idempotency_key: str | None = None
    ) -> dict[str, Any]:
        """Reactivate a cancelled purchase. Maps to POST /v1/sdk/purchases/{ref}/reactivate."""
        return await self._http.send(
            _RequestSpec(
                "POST",
                f"/v1/sdk/purchases/{purchase_ref}/reactivate",
                idempotency_key=idempotency_key,
            )
        )

    # --- Admin: Products ---

    async def list_products(self) -> list[Product]:
        """List all products. Maps to GET /v1/sdk/products."""
        data = await self._http.send(_RequestSpec("GET", "/v1/sdk/products"))
        items: list[Any] = data if isinstance(data, list) else data.get("products", [])
        return [Product.model_validate(p) for p in items]

    async def get_product(self, product_ref: str) -> Product:
        """Get a product by ref. Maps to GET /v1/sdk/products/{ref}."""
        data = await self._http.send(_RequestSpec("GET", f"/v1/sdk/products/{product_ref}"))
        return Product.model_validate(data)

    async def create_product(
        self, *, name: str, type: str, default_currency: str, idempotency_key: str | None = None
    ) -> Product:
        """Create a product. Maps to POST /v1/sdk/products."""
        req = CreateProductRequest(name=name, type=type, default_currency=default_currency)
        data = await self._http.send(
            _RequestSpec(
                "POST",
                "/v1/sdk/products",
                json=req.model_dump(by_alias=True, exclude_none=True),
                idempotency_key=idempotency_key,
            )
        )
        return Product.model_validate(data)

    async def delete_product(self, product_ref: str) -> dict[str, Any]:
        """Delete a product. Maps to DELETE /v1/sdk/products/{ref}."""
        return await self._http.send(_RequestSpec("DELETE", f"/v1/sdk/products/{product_ref}"))

    async def clone_product(
        self, product_ref: str, *, new_name: str, idempotency_key: str | None = None
    ) -> Product:
        """Clone a product with a new name. Maps to POST /v1/sdk/products/{ref}/clone."""
        req = CloneProductRequest(new_name=new_name)
        data = await self._http.send(
            _RequestSpec(
                "POST",
                f"/v1/sdk/products/{product_ref}/clone",
                json=req.model_dump(by_alias=True, exclude_none=True),
                idempotency_key=idempotency_key,
            )
        )
        return Product.model_validate(data)

    # --- Admin: Plans ---

    async def list_plans(self, product_ref: str) -> list[Plan]:
        """List plans for a product. Maps to GET /v1/sdk/products/{ref}/plans."""
        data = await self._http.send(_RequestSpec("GET", f"/v1/sdk/products/{product_ref}/plans"))
        items: list[Any] = data if isinstance(data, list) else data.get("plans", [])
        return [Plan.model_validate(p) for p in items]

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
        """Create a plan for a product. Maps to POST /v1/sdk/products/{ref}/plans."""
        req = CreatePlanRequest(
            name=name, type=type, price=price, currency=currency, interval=interval
        )
        data = await self._http.send(
            _RequestSpec(
                "POST",
                f"/v1/sdk/products/{product_ref}/plans",
                json=req.model_dump(by_alias=True, exclude_none=True),
                idempotency_key=idempotency_key,
            )
        )
        return Plan.model_validate(data)

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
        """Update a plan. Maps to PUT /v1/sdk/products/{ref}/plans/{ref}."""
        req = UpdatePlanRequest(
            name=name, type=type, price=price, currency=currency, interval=interval
        )
        data = await self._http.send(
            _RequestSpec(
                "PUT",
                f"/v1/sdk/products/{product_ref}/plans/{plan_ref}",
                json=req.model_dump(by_alias=True, exclude_none=True),
            )
        )
        return Plan.model_validate(data)

    async def delete_plan(self, product_ref: str, plan_ref: str) -> dict[str, Any]:
        """Delete a plan. Maps to DELETE /v1/sdk/products/{ref}/plans/{ref}."""
        return await self._http.send(
            _RequestSpec("DELETE", f"/v1/sdk/products/{product_ref}/plans/{plan_ref}")
        )

    # --- Admin: Merchant + Platform ---

    async def get_merchant(self) -> Merchant:
        """Get merchant account details. Maps to GET /v1/sdk/merchant."""
        data = await self._http.send(_RequestSpec("GET", "/v1/sdk/merchant"))
        return Merchant.model_validate(data)

    async def get_platform_config(self) -> PlatformConfig:
        """Get platform-level configuration. Maps to GET /v1/sdk/platform-config."""
        data = await self._http.send(_RequestSpec("GET", "/v1/sdk/platform-config"))
        return PlatformConfig.model_validate(data)
