"""OpSpec registry + path interpolation (HLD V1.5 locks: OR1-OR6)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from urllib.parse import quote


class RetrySafety(Enum):
    """HLD OR1: three dimensions of retry safety.

    NEVER    — mutating, server-non-idempotent (e.g. track_usage).
    WITH_KEY — safe to retry IFF Idempotency-Key present (e.g. ensure_customer).
    ALWAYS   — idempotent GET/PUT/DELETE; safe under any retry.
    """

    NEVER = "never"
    WITH_KEY = "with_key"
    ALWAYS = "always"


@dataclass(frozen=True)
class OpSpec:
    name: str
    method: str
    path_template: str
    retry_safety: RetrySafety
    auth_required: bool = True


def _interpolate(template: str, **kwargs: str) -> str:
    """URL-safe path param substitution (HLD OR2).

    Each {name} placeholder is replaced using urllib.parse.quote(value, safe='').
    Handles /, ?, #, spaces, unicode safely.
    """
    for key, value in kwargs.items():
        template = template.replace(f"{{{key}}}", quote(str(value), safe=""))
    return template


REGISTRY: dict[str, OpSpec] = {
    # Customers
    "customers.ensure": OpSpec(
        "customers.ensure", "POST", "/v1/sdk/customers", RetrySafety.WITH_KEY
    ),
    "customers.get": OpSpec(
        "customers.get", "GET", "/v1/sdk/customers/{customer_ref}", RetrySafety.ALWAYS
    ),
    "customers.update": OpSpec(
        "customers.update", "PATCH", "/v1/sdk/customers/{customer_ref}", RetrySafety.ALWAYS
    ),
    "customers.balance": OpSpec(
        "customers.balance", "GET", "/v1/sdk/customers/{customer_ref}/balance", RetrySafety.ALWAYS
    ),
    # Checkout
    "checkout.create_session": OpSpec(
        "checkout.create_session", "POST", "/v1/sdk/checkout-sessions", RetrySafety.WITH_KEY
    ),
    # Limits
    "limits.check": OpSpec("limits.check", "POST", "/v1/sdk/limits", RetrySafety.ALWAYS),
    # Purchases
    "purchases.cancel": OpSpec(
        "purchases.cancel",
        "POST",
        "/v1/sdk/purchases/{purchase_ref}/cancel",
        RetrySafety.WITH_KEY,
    ),
    "purchases.reactivate": OpSpec(
        "purchases.reactivate",
        "POST",
        "/v1/sdk/purchases/{purchase_ref}/reactivate",
        RetrySafety.WITH_KEY,
    ),
    # Usage
    "usage.track": OpSpec("usage.track", "POST", "/v1/sdk/usages", RetrySafety.NEVER),
    # Products
    "products.list": OpSpec("products.list", "GET", "/v1/sdk/products", RetrySafety.ALWAYS),
    "products.get": OpSpec(
        "products.get", "GET", "/v1/sdk/products/{product_ref}", RetrySafety.ALWAYS
    ),
    "products.create": OpSpec("products.create", "POST", "/v1/sdk/products", RetrySafety.WITH_KEY),
    "products.delete": OpSpec(
        "products.delete", "DELETE", "/v1/sdk/products/{product_ref}", RetrySafety.ALWAYS
    ),
    "products.clone": OpSpec(
        "products.clone",
        "POST",
        "/v1/sdk/products/{product_ref}/clone",
        RetrySafety.WITH_KEY,
    ),
    # Plans
    "plans.list": OpSpec(
        "plans.list", "GET", "/v1/sdk/products/{product_ref}/plans", RetrySafety.ALWAYS
    ),
    "plans.create": OpSpec(
        "plans.create", "POST", "/v1/sdk/products/{product_ref}/plans", RetrySafety.WITH_KEY
    ),
    "plans.update": OpSpec(
        "plans.update",
        "PUT",
        "/v1/sdk/products/{product_ref}/plans/{plan_ref}",
        RetrySafety.ALWAYS,
    ),
    "plans.delete": OpSpec(
        "plans.delete",
        "DELETE",
        "/v1/sdk/products/{product_ref}/plans/{plan_ref}",
        RetrySafety.ALWAYS,
    ),
    # Merchant + Platform
    "merchant.get": OpSpec("merchant.get", "GET", "/v1/sdk/merchant", RetrySafety.ALWAYS),
    "platform.get_config": OpSpec(
        "platform.get_config", "GET", "/v1/sdk/platform-config", RetrySafety.ALWAYS
    ),
}
