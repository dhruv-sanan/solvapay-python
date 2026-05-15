"""Typed pydantic models for SolvaPay webhook events.

Mirrors the 13 event types in @solvapay/server src/types/webhook.ts.
Use as a discriminated union with `verify_webhook(..., parse_as=WebhookEvent)`.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class _Event(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    id: str
    created: int
    api_version: str
    livemode: bool
    data: dict[str, Any]


class PaymentSucceeded(_Event):
    type: Literal["payment.succeeded"]


class PaymentFailed(_Event):
    type: Literal["payment.failed"]


class PaymentRefunded(_Event):
    type: Literal["payment.refunded"]


class PaymentRefundFailed(_Event):
    type: Literal["payment.refund_failed"]


class PurchaseCreated(_Event):
    type: Literal["purchase.created"]


class PurchaseUpdated(_Event):
    type: Literal["purchase.updated"]


class PurchaseCancelled(_Event):
    type: Literal["purchase.cancelled"]


class PurchaseExpired(_Event):
    type: Literal["purchase.expired"]


class PurchaseSuspended(_Event):
    type: Literal["purchase.suspended"]


class CustomerCreated(_Event):
    type: Literal["customer.created"]


class CustomerUpdated(_Event):
    type: Literal["customer.updated"]


class CustomerDeleted(_Event):
    type: Literal["customer.deleted"]


class CheckoutSessionCreated(_Event):
    type: Literal["checkout_session.created"]


WebhookEvent = Annotated[
    PaymentSucceeded
    | PaymentFailed
    | PaymentRefunded
    | PaymentRefundFailed
    | PurchaseCreated
    | PurchaseUpdated
    | PurchaseCancelled
    | PurchaseExpired
    | PurchaseSuspended
    | CustomerCreated
    | CustomerUpdated
    | CustomerDeleted
    | CheckoutSessionCreated,
    Field(discriminator="type"),
]
