"""Tests for typed webhook event discriminated union."""

from __future__ import annotations

import hashlib
import hmac
import json
import time

from solvapay import (
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
from solvapay.webhooks import verify_webhook

SECRET = "whsec_test_secret"


def _make_event(event_type: str) -> tuple[str, str]:
    payload = {
        "id": "evt_test",
        "type": event_type,
        "created": int(time.time()),
        "api_version": "2025-10-01",
        "livemode": False,
        "data": {},
    }
    body = json.dumps(payload)
    ts = int(time.time())
    h = hmac.new(SECRET.encode(), f"{ts}.{body}".encode(), hashlib.sha256).hexdigest()
    return body, f"t={ts},v1={h}"


def _verify_typed(event_type: str) -> WebhookEvent:  # type: ignore[return]
    body, sig = _make_event(event_type)
    return verify_webhook(body=body, signature=sig, secret=SECRET, parse_as=WebhookEvent)  # type: ignore[return-value]


def test_payment_succeeded() -> None:
    event = _verify_typed("payment.succeeded")
    assert isinstance(event, PaymentSucceeded)
    assert event.type == "payment.succeeded"


def test_payment_failed() -> None:
    event = _verify_typed("payment.failed")
    assert isinstance(event, PaymentFailed)


def test_payment_refunded() -> None:
    event = _verify_typed("payment.refunded")
    assert isinstance(event, PaymentRefunded)


def test_payment_refund_failed() -> None:
    event = _verify_typed("payment.refund_failed")
    assert isinstance(event, PaymentRefundFailed)


def test_purchase_created() -> None:
    event = _verify_typed("purchase.created")
    assert isinstance(event, PurchaseCreated)


def test_purchase_updated() -> None:
    event = _verify_typed("purchase.updated")
    assert isinstance(event, PurchaseUpdated)


def test_purchase_cancelled() -> None:
    event = _verify_typed("purchase.cancelled")
    assert isinstance(event, PurchaseCancelled)


def test_purchase_expired() -> None:
    event = _verify_typed("purchase.expired")
    assert isinstance(event, PurchaseExpired)


def test_purchase_suspended() -> None:
    event = _verify_typed("purchase.suspended")
    assert isinstance(event, PurchaseSuspended)


def test_customer_created() -> None:
    event = _verify_typed("customer.created")
    assert isinstance(event, CustomerCreated)


def test_customer_updated() -> None:
    event = _verify_typed("customer.updated")
    assert isinstance(event, CustomerUpdated)


def test_customer_deleted() -> None:
    event = _verify_typed("customer.deleted")
    assert isinstance(event, CustomerDeleted)


def test_checkout_session_created() -> None:
    event = _verify_typed("checkout_session.created")
    assert isinstance(event, CheckoutSessionCreated)


def test_verify_webhook_returns_dict_without_parse_as() -> None:
    body, sig = _make_event("purchase.created")
    result = verify_webhook(body=body, signature=sig, secret=SECRET)
    assert isinstance(result, dict)
    assert result["type"] == "purchase.created"
