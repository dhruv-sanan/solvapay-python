"""Public SolvaPay client. Synchronous; mirrors @solvapay/core surface."""

from __future__ import annotations

import time
from typing import Any

from solvapay._config import resolve_api_key, resolve_base_url
from solvapay._http import HttpClient
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


class SolvaPay:
    """Synchronous SolvaPay API client.

    Args:
        api_key: SolvaPay secret key. Falls back to SOLVAPAY_SECRET_KEY env var.
        base_url: API base URL. Falls back to SOLVAPAY_API_BASE_URL env var,
                  then to https://api.solvapay.com.
        timeout: HTTP timeout in seconds. Default 30.

    Example:
        >>> from solvapay import SolvaPay
        >>> sv = SolvaPay()  # reads SOLVAPAY_SECRET_KEY
        >>> session = sv.create_checkout_session(
        ...     customer_ref="cus_123", product_ref="prd_0QKI8NHF"
        ... )
        >>> print(session.checkout_url)
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._http = HttpClient(
            api_key=resolve_api_key(api_key),
            base_url=resolve_base_url(base_url),
            timeout=timeout,
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> SolvaPay:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def create_checkout_session(
        self,
        *,
        customer_ref: str,
        product_ref: str,
        plan_ref: str | None = None,
        return_url: str | None = None,
    ) -> CheckoutSession:
        """Create a hosted checkout session.

        Maps to POST /v1/sdk/checkout-sessions.

        Args:
            customer_ref: Backend customer reference.
            product_ref: SolvaPay product reference (e.g., "prd_0QKI8NHF").
            plan_ref: Optional plan reference. Omit to show plan selector.
            return_url: Optional URL to redirect after checkout.

        Returns:
            CheckoutSession with .session_id and .checkout_url.
        """
        req = CheckoutSessionRequest(
            customer_ref=customer_ref,
            product_ref=product_ref,
            plan_ref=plan_ref,
            return_url=return_url,
        )
        data = self._http.request(
            "POST",
            "/v1/sdk/checkout-sessions",
            json=req.model_dump(by_alias=True, exclude_none=True),
        )
        return CheckoutSession.model_validate(data)

    def ensure_customer(
        self,
        customer_ref: str,
        external_ref: str | None = None,
        *,
        email: str | None = None,
        name: str | None = None,
    ) -> str:
        """Idempotently create or look up a customer.

        Tries GET /v1/sdk/customers?externalRef=... first. On 404, creates via
        POST /v1/sdk/customers. Auto-generates a placeholder email if not provided.

        Returns the SolvaPay backend customer reference string.
        """
        lookup_ref = external_ref or customer_ref
        try:
            existing = self._http.request(
                "GET", "/v1/sdk/customers", params={"externalRef": lookup_ref}
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
        created = self._http.request(
            "POST",
            "/v1/sdk/customers",
            json=req.model_dump(by_alias=True, exclude_none=True),
        )
        ref = created.get("reference") or created.get("customerRef")
        if not ref:
            raise SolvaPayAPIError(200, f"customer create returned no reference: {created!r}")
        return str(ref)

    def get_customer(
        self,
        customer_ref: str | None = None,
        *,
        external_ref: str | None = None,
        email: str | None = None,
    ) -> Customer:
        """Retrieve a customer by ref, external_ref, or email."""
        if customer_ref:
            data = self._http.request("GET", f"/v1/sdk/customers/{customer_ref}")
        elif external_ref:
            data = self._http.request(
                "GET", "/v1/sdk/customers", params={"externalRef": external_ref}
            )
        elif email:
            data = self._http.request("GET", "/v1/sdk/customers", params={"email": email})
        else:
            raise ValueError("Must provide customer_ref, external_ref, or email")
        return Customer.model_validate(data)

    def check_limits(
        self,
        *,
        customer_ref: str,
        product_ref: str,
        plan_ref: str | None = None,
        meter_name: str | None = None,
        usage_type: str | None = None,
    ) -> LimitResponse:
        """Check whether a customer is within their purchase/usage limits.

        Maps to POST /v1/sdk/limits.
        """
        req = CheckLimitsRequest(
            customer_ref=customer_ref,
            product_ref=product_ref,
            plan_ref=plan_ref,
            meter_name=meter_name,
            usage_type=usage_type,
        )
        data = self._http.request(
            "POST",
            "/v1/sdk/limits",
            json=req.model_dump(by_alias=True, exclude_none=True),
        )
        return LimitResponse.model_validate(data)

    def track_usage(
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
        return self._http.request(
            "POST",
            "/v1/sdk/usages",
            json=req.model_dump(by_alias=True, exclude_none=True),
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
        """Update customer fields. Maps to PATCH /v1/sdk/customers/{ref}."""
        req = UpdateCustomerRequest(email=email, name=name, external_ref=external_ref)
        data = self._http.request(
            "PATCH",
            f"/v1/sdk/customers/{customer_ref}",
            json=req.model_dump(by_alias=True, exclude_none=True),
        )
        return Customer.model_validate(data)

    def get_customer_balance(self, customer_ref: str) -> BalanceResponse:
        """Get credit balance for a customer. Maps to GET /v1/sdk/customers/{ref}/balance."""
        data = self._http.request("GET", f"/v1/sdk/customers/{customer_ref}/balance")
        return BalanceResponse.model_validate(data)

    def cancel_purchase(self, purchase_ref: str, *, reason: str | None = None) -> dict[str, Any]:
        """Cancel a purchase. Maps to POST /v1/sdk/purchases/{ref}/cancel."""
        req = CancelPurchaseRequest(reason=reason)
        return self._http.request(
            "POST",
            f"/v1/sdk/purchases/{purchase_ref}/cancel",
            json=req.model_dump(by_alias=True, exclude_none=True),
        )

    def reactivate_purchase(self, purchase_ref: str) -> dict[str, Any]:
        """Reactivate a cancelled purchase. Maps to POST /v1/sdk/purchases/{ref}/reactivate."""
        return self._http.request("POST", f"/v1/sdk/purchases/{purchase_ref}/reactivate")

    # --- Admin: Products ---

    def list_products(self) -> list[Product]:
        """List all products. Maps to GET /v1/sdk/products."""
        data = self._http.request("GET", "/v1/sdk/products")
        items: list[Any] = data if isinstance(data, list) else data.get("products", [])
        return [Product.model_validate(p) for p in items]

    def get_product(self, product_ref: str) -> Product:
        """Get a product by ref. Maps to GET /v1/sdk/products/{ref}."""
        data = self._http.request("GET", f"/v1/sdk/products/{product_ref}")
        return Product.model_validate(data)

    def create_product(self, *, name: str, type: str, default_currency: str) -> Product:
        """Create a product. Maps to POST /v1/sdk/products."""
        req = CreateProductRequest(name=name, type=type, default_currency=default_currency)
        data = self._http.request(
            "POST",
            "/v1/sdk/products",
            json=req.model_dump(by_alias=True, exclude_none=True),
        )
        return Product.model_validate(data)

    def delete_product(self, product_ref: str) -> dict[str, Any]:
        """Delete a product. Maps to DELETE /v1/sdk/products/{ref}."""
        return self._http.request("DELETE", f"/v1/sdk/products/{product_ref}")

    def clone_product(self, product_ref: str, *, new_name: str) -> Product:
        """Clone a product with a new name. Maps to POST /v1/sdk/products/{ref}/clone."""
        req = CloneProductRequest(new_name=new_name)
        data = self._http.request(
            "POST",
            f"/v1/sdk/products/{product_ref}/clone",
            json=req.model_dump(by_alias=True, exclude_none=True),
        )
        return Product.model_validate(data)

    # --- Admin: Plans ---

    def list_plans(self, product_ref: str) -> list[Plan]:
        """List plans for a product. Maps to GET /v1/sdk/products/{ref}/plans."""
        data = self._http.request("GET", f"/v1/sdk/products/{product_ref}/plans")
        items: list[Any] = data if isinstance(data, list) else data.get("plans", [])
        return [Plan.model_validate(p) for p in items]

    def create_plan(
        self,
        product_ref: str,
        *,
        name: str,
        type: str,
        price: float | None = None,
        currency: str | None = None,
        interval: str | None = None,
    ) -> Plan:
        """Create a plan for a product. Maps to POST /v1/sdk/products/{ref}/plans."""
        req = CreatePlanRequest(
            name=name, type=type, price=price, currency=currency, interval=interval
        )
        data = self._http.request(
            "POST",
            f"/v1/sdk/products/{product_ref}/plans",
            json=req.model_dump(by_alias=True, exclude_none=True),
        )
        return Plan.model_validate(data)

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
        """Update a plan. Maps to PUT /v1/sdk/products/{ref}/plans/{ref}."""
        req = UpdatePlanRequest(
            name=name, type=type, price=price, currency=currency, interval=interval
        )
        data = self._http.request(
            "PUT",
            f"/v1/sdk/products/{product_ref}/plans/{plan_ref}",
            json=req.model_dump(by_alias=True, exclude_none=True),
        )
        return Plan.model_validate(data)

    def delete_plan(self, product_ref: str, plan_ref: str) -> dict[str, Any]:
        """Delete a plan. Maps to DELETE /v1/sdk/products/{ref}/plans/{ref}."""
        return self._http.request("DELETE", f"/v1/sdk/products/{product_ref}/plans/{plan_ref}")

    # --- Admin: Merchant + Platform ---

    def get_merchant(self) -> Merchant:
        """Get merchant account details. Maps to GET /v1/sdk/merchant."""
        data = self._http.request("GET", "/v1/sdk/merchant")
        return Merchant.model_validate(data)

    def get_platform_config(self) -> PlatformConfig:
        """Get platform-level configuration. Maps to GET /v1/sdk/platform-config."""
        data = self._http.request("GET", "/v1/sdk/platform-config")
        return PlatformConfig.model_validate(data)
