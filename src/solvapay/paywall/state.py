"""Paywall state re-export from top-level paywall_state module (backward compat)."""

from __future__ import annotations

from solvapay.paywall_state import (
    GateDecision,
    PaywallState,
    build_gate_message,
    build_nudge_message,
    classify_state,
    decide,
    gate,
)

__all__ = [
    "PaywallState",
    "GateDecision",
    "classify_state",
    "decide",
    "gate",
    "build_gate_message",
    "build_nudge_message",
]
