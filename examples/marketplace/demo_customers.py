"""Two real sandbox customers. Resolved from env at startup.

Customer A: pre-existing in SolvaPay sandbox, subscribed to the Pro plan.
Customer B: pre-existing in SolvaPay sandbox, no subscription — hits free
            tier limit so check_limits returns a paywall state.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DemoCustomer:
    key: str
    customer_ref: str
    name: str


def load_customers() -> dict[str, DemoCustomer]:
    a_ref = os.environ.get("SOLVAPAY_DEMO_CUSTOMER_REF", "cus_CI5SGXJF")
    b_ref = os.environ.get("SOLVAPAY_DEMO_BLOCKED_CUSTOMER_REF", "cus_YARKQDEN")
    return {
        "alice": DemoCustomer(key="alice", customer_ref=a_ref, name="Alice"),
        "bob": DemoCustomer(key="bob", customer_ref=b_ref, name="Bob"),
    }
