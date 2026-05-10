"""Public SolvaPay client. Synchronous; mirrors @solvapay/core surface."""
from __future__ import annotations

import time

from solvapay._config import resolve_api_key, resolve_base_url
from solvapay._http import HttpClient
from solvapay.exceptions import SolvaPayAPIError
from solvapay.models import (
    CheckLimitsRequest,
    CheckoutSession,
    CheckoutSessionRequest,
    CreateCustomerRequest,
    Customer,
    LimitResponse,
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
            if existing.get("customerRef"):
                return str(existing["customerRef"])
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
        return str(created["customerRef"])

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
            data = self._http.request(
                "GET", "/v1/sdk/customers", params={"email": email}
            )
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
