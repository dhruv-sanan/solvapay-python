"""Pydantic models for SolvaPay API request/response payloads.

Python fields are snake_case. API wire format is camelCase.
Field(alias="camelCase") handles the mapping; populate_by_name=True
lets callers use either form during construction.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class CheckoutSession(_Base):
    """Response from POST /v1/sdk/checkout-sessions."""

    session_id: str = Field(alias="sessionId")
    checkout_url: str = Field(alias="checkoutUrl")


class Purchase(_Base):
    reference: str
    product_name: str | None = Field(default=None, alias="productName")
    product_ref: str | None = Field(default=None, alias="productRef")
    plan_ref: str | None = Field(default=None, alias="planRef")
    status: str
    start_date: str = Field(alias="startDate")
    end_date: str | None = Field(default=None, alias="endDate")
    amount: int | None = None
    currency: str | None = None
    cancelled_at: str | None = Field(default=None, alias="cancelledAt")


class Customer(_Base):
    customer_ref: str = Field(alias="customerRef")
    email: str | None = None
    name: str | None = None
    external_ref: str | None = Field(default=None, alias="externalRef")
    purchases: list[Purchase] | None = None


class LimitResponse(_Base):
    within_limits: bool = Field(alias="withinLimits")
    remaining: float = 0
    plan: str | None = None
    checkout_url: str | None = Field(default=None, alias="checkoutUrl")
    meter_name: str | None = Field(default=None, alias="meterName")
    credit_balance: float | None = Field(default=None, alias="creditBalance")
    credits_per_unit: float | None = Field(default=None, alias="creditsPerUnit")
    currency: str | None = None


# ---------------------------------------------------------------------------
# Request models — snake_case Python fields, camelCase wire via alias
# ---------------------------------------------------------------------------


class CheckoutSessionRequest(_Base):
    customer_ref: str = Field(serialization_alias="customerRef")
    product_ref: str = Field(serialization_alias="productRef")
    plan_ref: str | None = Field(default=None, serialization_alias="planRef")
    return_url: str | None = Field(default=None, serialization_alias="returnUrl")


class CreateCustomerRequest(_Base):
    email: str
    external_ref: str = Field(serialization_alias="externalRef")
    name: str | None = None


class CheckLimitsRequest(_Base):
    customer_ref: str = Field(serialization_alias="customerRef")
    product_ref: str = Field(serialization_alias="productRef")
    plan_ref: str | None = Field(default=None, serialization_alias="planRef")
    meter_name: str | None = Field(default=None, serialization_alias="meterName")
    usage_type: str | None = Field(default=None, serialization_alias="usageType")


class TrackUsageRequest(_Base):
    customer_ref: str = Field(serialization_alias="customerRef")
    product_ref: str = Field(serialization_alias="productRef")
    meter_name: str = Field(serialization_alias="meterName")
    units: float


class UpdateCustomerRequest(_Base):
    email: str | None = None
    name: str | None = None
    external_ref: str | None = Field(default=None, serialization_alias="externalRef")


class BalanceResponse(_Base):
    customer_ref: str = Field(alias="customerRef")
    balance: float
    currency: str
    plan: str | None = None


class CancelPurchaseRequest(_Base):
    reason: str | None = None


# ---------------------------------------------------------------------------
# Admin response models
# ---------------------------------------------------------------------------


class Product(_Base):
    """A SolvaPay product."""

    reference: str
    name: str
    type: str
    status: str | None = None
    default_currency: str | None = Field(default=None, alias="defaultCurrency")
    created_at: str | None = Field(default=None, alias="createdAt")


class Plan(_Base):
    """A SolvaPay plan attached to a product."""

    reference: str
    name: str
    type: str
    price: float | None = None
    currency: str | None = None
    interval: str | None = None
    status: str | None = None
    product_ref: str | None = Field(default=None, alias="productRef")


class Merchant(_Base):
    """Merchant account details."""

    merchant_ref: str | None = Field(default=None, alias="merchantRef")
    name: str | None = None
    email: str | None = None


class PlatformConfig(_Base):
    """Platform-level configuration."""

    currency: str | None = None


# ---------------------------------------------------------------------------
# Admin request models
# ---------------------------------------------------------------------------


class CreateProductRequest(_Base):
    name: str
    type: str
    default_currency: str = Field(serialization_alias="defaultCurrency")


class CreatePlanRequest(_Base):
    name: str
    type: str
    price: float | None = None
    currency: str | None = None
    interval: str | None = None


class UpdatePlanRequest(_Base):
    name: str | None = None
    type: str | None = None
    price: float | None = None
    currency: str | None = None
    interval: str | None = None


class CloneProductRequest(_Base):
    new_name: str = Field(serialization_alias="newName")
