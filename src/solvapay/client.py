"""Public SolvaPay client. Synchronous; mirrors @solvapay/core surface."""
from __future__ import annotations

from solvapay._config import resolve_api_key, resolve_base_url
from solvapay._http import HttpClient
from solvapay.models import CheckoutSession


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

        Maps to POST /v1/sdk/checkout-sessions on the SolvaPay API.

        Args:
            customer_ref: Backend customer reference (from ensure_customer or your DB).
            product_ref: SolvaPay product reference (e.g., "prd_0QKI8NHF").
            plan_ref: Optional plan reference. Omit to show plan selector to customer.
            return_url: Optional URL to redirect to after checkout.

        Returns:
            CheckoutSession with .session_id and .checkout_url.
        """
        body: dict[str, str] = {"customerRef": customer_ref, "productRef": product_ref}
        if plan_ref is not None:
            body["planRef"] = plan_ref
        if return_url is not None:
            body["returnUrl"] = return_url
        data = self._http.request("POST", "/v1/sdk/checkout-sessions", json=body)
        return CheckoutSession.model_validate(data)
