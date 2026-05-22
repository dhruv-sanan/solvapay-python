"""SolvaPay community Python SDK."""

from __future__ import annotations

from solvapay import paywall
from solvapay._async_client import AsyncSolvaPay
from solvapay._stability import MANIFEST, deprecated, experimental, stable
from solvapay.client import SolvaPay
from solvapay.events import (
    CheckoutSessionCreated,
    CustomerCreated,
    CustomerDeleted,
    CustomerUpdated,
    PaymentFailed,
    PaymentRefunded,
    PaymentRefundFailed,
    PaymentSucceeded,
    PurchaseCancelled,
    PurchaseCreated,
    PurchaseExpired,
    PurchaseSuspended,
    PurchaseUpdated,
    WebhookEvent,
)
from solvapay.exceptions import (
    APIConnectionError,
    APIError,
    APIServerError,
    APITimeoutError,
    AuthenticationError,
    InvalidRequestError,
    NotFoundError,
    PermissionError,
    RateLimitError,
    SolvaPayAPIError,
    SolvaPayError,
)
from solvapay.models import BalanceResponse, Merchant, Plan, PlatformConfig, Product
from solvapay.paywall import PaywallRequired
from solvapay.webhooks import verify_webhook

# Register stable exports in MANIFEST (HLD V1.2).
# stable(X) returns X unchanged — isinstance() continues to work (HLD SM1).
stable(SolvaPay)
stable(AsyncSolvaPay)
stable(SolvaPayError)
stable(APIError)
stable(AuthenticationError)
stable(PermissionError)
stable(NotFoundError)
stable(RateLimitError)
stable(InvalidRequestError)
stable(APIServerError)
stable(APIConnectionError)
stable(APITimeoutError)
stable(PaywallRequired)
stable(verify_webhook)
stable(BalanceResponse)
stable(Product)
stable(Plan)
stable(Merchant)
stable(PlatformConfig)
stable(WebhookEvent)
# SolvaPayAPIError is a back-compat alias — deprecated in v1.0, removed v2.0
deprecated(removed_in="2.0")(SolvaPayAPIError)

__all__ = [
    "APIConnectionError",
    "APIError",
    "APIServerError",
    "APITimeoutError",
    "AsyncSolvaPay",
    "AuthenticationError",
    "BalanceResponse",
    "CheckoutSessionCreated",
    "CustomerCreated",
    "CustomerDeleted",
    "CustomerUpdated",
    "InvalidRequestError",
    "MANIFEST",
    "Merchant",
    "NotFoundError",
    "PaymentFailed",
    "PaymentRefundFailed",
    "PaymentRefunded",
    "PaymentSucceeded",
    "PaywallRequired",
    "PermissionError",
    "Plan",
    "PlatformConfig",
    "Product",
    "PurchaseCancelled",
    "PurchaseCreated",
    "PurchaseExpired",
    "PurchaseSuspended",
    "PurchaseUpdated",
    "RateLimitError",
    "SolvaPay",
    "SolvaPayAPIError",
    "SolvaPayError",
    "WebhookEvent",
    "deprecated",
    "experimental",
    "paywall",
    "stable",
    "verify_webhook",
]
__version__ = "0.7.2"
