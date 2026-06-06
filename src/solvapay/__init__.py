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
from solvapay.webhooks import sign_webhook, verify_webhook

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
stable(sign_webhook)
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
    "MANIFEST",
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
    # adapters exposed lazily via __getattr__ below (PEP 562)
    "adapters",
    "deprecated",
    "experimental",
    "paywall",
    "sign_webhook",
    "stable",
    "verify_webhook",
]
__version__ = "0.9.1"

# PEP 562 — lazy adapter submodule access.
# Adapters drag in optional heavy deps (fastmcp, langchain-core, fastapi).
# __getattr__ defers their load until first access; they never load on bare
# `import solvapay` for users who don't use framework adapters.
_LAZY_MODULES = {
    "adapters": "solvapay.adapters",
}


def __getattr__(name: str) -> object:
    if name in _LAZY_MODULES:
        import importlib

        mod = importlib.import_module(_LAZY_MODULES[name])
        globals()[name] = mod
        return mod
    raise AttributeError(f"module 'solvapay' has no attribute {name!r}")


def __dir__() -> list[str]:
    # PEP 562: include lazy names alongside normal module attrs.
    return sorted(set(globals()) | set(_LAZY_MODULES))
