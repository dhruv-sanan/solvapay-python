"""Pure-function paywall state machine. Mirrors TS classifyPaywallState.

Input: a LimitResponse (output of check_limits).
Output: a structured state + display copy + recovery action.
"""

from __future__ import annotations

from enum import Enum
from typing import NamedTuple

from solvapay.models import LimitResponse


class PaywallState(str, Enum):
    OK = "ok"
    ACTIVATION_REQUIRED = "activation_required"
    TOPUP_REQUIRED = "topup_required"
    UPGRADE_REQUIRED = "upgrade_required"
    REACTIVATION_REQUIRED = "reactivation_required"  # reserved; not yet returned by classify_state


class GateDecision(NamedTuple):
    state: PaywallState
    message: str
    recovery_tool: str | None  # "upgrade" | "topup" | "activate_plan" | "manage_account" | None
    checkout_url: str | None


_RECOVERY_TOOL: dict[PaywallState, str | None] = {
    PaywallState.OK: None,
    PaywallState.ACTIVATION_REQUIRED: "activate_plan",
    PaywallState.TOPUP_REQUIRED: "topup",
    PaywallState.UPGRADE_REQUIRED: "upgrade",
    PaywallState.REACTIVATION_REQUIRED: "manage_account",
}


def classify_state(limits: LimitResponse) -> PaywallState:
    """Return the recovery state implied by a check_limits response.

    Precedence mirrors TS classifyPaywallState (paywall-state.ts):
    1. within_limits → OK
    2. plan is None → activation_required (no active plan; proxy for activationRequired flag)
    3. credit_balance present and exhausted → topup_required (usage-based, out of credits)
    4. everything else → upgrade_required (recurring cap or unresolvable state)
    """
    if limits.within_limits:
        return PaywallState.OK
    if limits.plan is None:
        return PaywallState.ACTIVATION_REQUIRED
    # Usage-based: credit_balance field signals usage-based billing in our LimitResponse.
    # Mirrors TS: creditBalance === 0 on a usage-based plan → topup path.
    if limits.credit_balance is not None and limits.credit_balance <= 0:
        return PaywallState.TOPUP_REQUIRED
    return PaywallState.UPGRADE_REQUIRED


def build_gate_message(state: PaywallState, limits: LimitResponse) -> str:
    """Terminal-friendly gate copy. Mirrors TS buildGateMessage.

    Inlines checkoutUrl when present so terminal-only MCP/CLI hosts can
    open a browser directly, matching TS behaviour exactly.
    """
    if state == PaywallState.OK:
        return ""
    url = limits.checkout_url or None
    open_clause = f", or open {url} in a browser" if url else ""
    if state == PaywallState.ACTIVATION_REQUIRED:
        return (
            f"Your plan needs activation before you can use this tool. "
            f"Call the `activate_plan` tool to activate it{open_clause}."
        )
    if state == PaywallState.TOPUP_REQUIRED:
        return f"You're out of credits. Call the `topup` tool to add more{open_clause}."
    if state == PaywallState.UPGRADE_REQUIRED:
        return (
            f"You don't have an active plan for this tool. "
            f"Call the `upgrade` tool to pick a plan{open_clause}."
        )
    # reactivation_required — two alternatives; URL not appended (mirrors TS)
    return (
        "Your previous plan is no longer active. "
        "Call the `manage_account` tool to reactivate it, "
        "or the `upgrade` tool to pick a new plan."
    )


def build_nudge_message(state: PaywallState, limits: LimitResponse) -> str:
    """Low-balance / approaching-cap nudge copy. Mirrors TS buildNudgeMessage.

    Only topup_required and upgrade_required produce actionable nudges on
    successful calls; other states return an empty string.
    """
    if state == PaywallState.OK:
        return ""
    url = limits.checkout_url or None
    visit_clause = f", or visit {url}" if url else ""
    if state == PaywallState.TOPUP_REQUIRED:
        return (
            f"Heads up — running low on credits. Call the `topup` tool to add more{visit_clause}."
        )
    if state == PaywallState.UPGRADE_REQUIRED:
        return (
            f"Heads up — approaching your plan's limit this period. "
            f"Call the `upgrade` tool for more headroom{visit_clause}."
        )
    if state == PaywallState.ACTIVATION_REQUIRED:
        return f"Heads up — this plan still needs activation. Call the `activate_plan` tool{visit_clause}."
    return f"Heads up — your plan is no longer active. Call the `manage_account` tool to reactivate it{visit_clause}."


def decide(limits: LimitResponse) -> GateDecision:
    """Full decision: state + gate message + recovery tool + checkout URL."""
    state = classify_state(limits)
    return GateDecision(
        state=state,
        message=build_gate_message(state, limits),
        recovery_tool=_RECOVERY_TOOL[state],
        checkout_url=limits.checkout_url,
    )
