"""Real SolvaPay SDK gateway. No mocking.

- Singleton SolvaPay() client against sandbox base URL.
- bootstrap_customer_b() returns pre-existing blocked demo customer ref.
- check_and_decide() uses the SDK's `paywall_state.gate()` helper which
  internally calls check_limits + (on block) create_checkout_session +
  get_customer to enrich the response, then classifies.
- record_usage() and fetch_balance() hit the real API.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache

from solvapay import SolvaPay
from solvapay.paywall_state import GateDecision, gate

log = logging.getLogger("marketplace.solvapay")


def product_ref() -> str:
    return os.environ.get("SOLVAPAY_PRODUCT_REF", "prd_0QKI8NHF")


@lru_cache(maxsize=1)
def get_client() -> SolvaPay:
    return SolvaPay(
        api_key=os.environ["SOLVAPAY_SECRET_KEY"],
        base_url=os.environ.get("SOLVAPAY_API_BASE_URL", "https://api.solvapay.com"),
    )


def bootstrap_customer_b() -> str:
    """Return the blocked demo customer ref. Customer is pre-existing in sandbox."""
    return os.environ.get("SOLVAPAY_DEMO_BLOCKED_CUSTOMER_REF", "cus_YARKQDEN")


def check_and_decide(*, customer_ref: str) -> GateDecision:
    """Hit /v1/sdk/limits + enrich + classify. Returns a fully actionable GateDecision."""
    decision = gate(get_client(), customer_ref=customer_ref, product_ref=product_ref())
    log.info(
        "SOLVAPAY gate | customer=%s | state=%s | within_limits=%s",
        customer_ref,
        decision.state.name,
        decision.state.name == "OK",
    )
    return decision


def record_usage(*, customer_ref: str, units: float = 1.0, meter_name: str = "requests") -> None:
    log.info("SOLVAPAY track_usage | customer=%s | units=%s | meter=%s", customer_ref, units, meter_name)
    get_client().track_usage(
        customer_ref=customer_ref,
        product_ref=product_ref(),
        meter_name=meter_name,
        units=units,
    )


def fetch_balance(customer_ref: str) -> float | None:
    try:
        return float(get_client().get_customer_balance(customer_ref).balance)
    except Exception:
        return None


def fetch_remaining(customer_ref: str) -> tuple[bool, float, str | None]:
    """Return (within_limits, remaining, meter_name) for sidebar display."""
    limits = get_client().check_limits(customer_ref=customer_ref, product_ref=product_ref())
    return limits.within_limits, float(limits.remaining), limits.meter_name


def fetch_customer_plan(customer_ref: str) -> str | None:
    """Best-effort: read plan name from the active purchase, if any."""
    try:
        customer = get_client().get_customer(customer_ref)
        if customer.purchases:
            for p in customer.purchases:
                if p.status == "active":
                    return p.plan_ref or p.product_name or "active"
    except Exception:
        pass
    return None
