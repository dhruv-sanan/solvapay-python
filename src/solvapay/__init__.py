"""SolvaPay community Python SDK."""

from __future__ import annotations

from solvapay import paywall
from solvapay._async_client import AsyncSolvaPay
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
    "paywall",
    "verify_webhook",
]
__version__ = "0.7.2"
