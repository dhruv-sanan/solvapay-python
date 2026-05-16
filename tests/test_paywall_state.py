"""Tests for paywall_state — pure-function state classifier."""

from __future__ import annotations

from solvapay.models import LimitResponse
from solvapay.paywall_state import (
    GateDecision,
    PaywallState,
    build_gate_message,
    build_nudge_message,
    classify_state,
    decide,
)


def _limit(**kwargs: object) -> LimitResponse:
    defaults: dict[str, object] = {"within_limits": False, "remaining": 0}
    defaults.update(kwargs)
    return LimitResponse.model_validate(defaults)


# ---------------------------------------------------------------------------
# classify_state — one test per enum value path
# ---------------------------------------------------------------------------


def test_classify_ok() -> None:
    limits = _limit(within_limits=True, remaining=10, plan="pln_basic")
    assert classify_state(limits) == PaywallState.OK


def test_classify_activation_required() -> None:
    limits = _limit(within_limits=False, plan=None)
    assert classify_state(limits) == PaywallState.ACTIVATION_REQUIRED


def test_classify_topup_required_zero_balance() -> None:
    limits = _limit(within_limits=False, plan="pln_usage", credit_balance=0.0)
    assert classify_state(limits) == PaywallState.TOPUP_REQUIRED


def test_classify_upgrade_required_recurring_cap() -> None:
    limits = _limit(within_limits=False, plan="pln_basic", remaining=0)
    assert classify_state(limits) == PaywallState.UPGRADE_REQUIRED


def test_classify_upgrade_required_no_credit_field() -> None:
    # plan is set, credit_balance absent → not usage-based → upgrade
    limits = _limit(within_limits=False, plan="pln_basic", credit_balance=None)
    assert classify_state(limits) == PaywallState.UPGRADE_REQUIRED


# ---------------------------------------------------------------------------
# build_gate_message — reactivation_required path (enum value coverage)
# ---------------------------------------------------------------------------


def test_build_gate_message_reactivation_required() -> None:
    limits = _limit(within_limits=False, plan="pln_old")
    msg = build_gate_message(PaywallState.REACTIVATION_REQUIRED, limits)
    assert "manage_account" in msg
    assert "upgrade" in msg


def test_build_gate_message_includes_url() -> None:
    limits = _limit(
        within_limits=False,
        plan=None,
        checkout_url="https://solvapay.com/c/activate",
    )
    msg = build_gate_message(PaywallState.ACTIVATION_REQUIRED, limits)
    assert "https://solvapay.com/c/activate" in msg


def test_build_gate_message_ok_returns_empty() -> None:
    limits = _limit(within_limits=True, plan="pln_basic")
    assert build_gate_message(PaywallState.OK, limits) == ""


# ---------------------------------------------------------------------------
# decide() — round-trip: state + message + recovery_tool + checkout_url
# ---------------------------------------------------------------------------


def test_decide_topup_round_trip() -> None:
    limits = _limit(
        within_limits=False,
        plan="pln_usage",
        credit_balance=0.0,
        checkout_url="https://solvapay.com/c/topup",
    )
    d: GateDecision = decide(limits)
    assert d.state == PaywallState.TOPUP_REQUIRED
    assert d.recovery_tool == "topup"
    assert d.checkout_url == "https://solvapay.com/c/topup"
    assert "topup" in d.message


def test_decide_ok_no_recovery_tool() -> None:
    limits = _limit(within_limits=True, remaining=5, plan="pln_basic")
    d = decide(limits)
    assert d.state == PaywallState.OK
    assert d.recovery_tool is None
    assert d.message == ""


# ---------------------------------------------------------------------------
# build_nudge_message — one test per branch
# ---------------------------------------------------------------------------


def test_nudge_ok_returns_empty() -> None:
    limits = _limit(within_limits=True, plan="pln_basic")
    assert build_nudge_message(PaywallState.OK, limits) == ""


def test_nudge_topup_required() -> None:
    limits = _limit(within_limits=False, plan="pln_usage", credit_balance=0.0)
    msg = build_nudge_message(PaywallState.TOPUP_REQUIRED, limits)
    assert "topup" in msg
    assert "Heads up" in msg


def test_nudge_upgrade_required() -> None:
    limits = _limit(within_limits=False, plan="pln_basic")
    msg = build_nudge_message(PaywallState.UPGRADE_REQUIRED, limits)
    assert "upgrade" in msg
    assert "Heads up" in msg


def test_nudge_activation_required() -> None:
    limits = _limit(within_limits=False, plan=None)
    msg = build_nudge_message(PaywallState.ACTIVATION_REQUIRED, limits)
    assert "activate_plan" in msg
    assert "Heads up" in msg


def test_nudge_reactivation_required() -> None:
    limits = _limit(within_limits=False, plan="pln_old")
    msg = build_nudge_message(PaywallState.REACTIVATION_REQUIRED, limits)
    assert "manage_account" in msg
    assert "Heads up" in msg


def test_nudge_includes_url_when_present() -> None:
    limits = _limit(
        within_limits=False,
        plan="pln_usage",
        credit_balance=0.0,
        checkout_url="https://solvapay.com/c/topup",
    )
    msg = build_nudge_message(PaywallState.TOPUP_REQUIRED, limits)
    assert "https://solvapay.com/c/topup" in msg


def test_nudge_no_url_clause_when_absent() -> None:
    limits = _limit(within_limits=False, plan="pln_basic")
    msg = build_nudge_message(PaywallState.UPGRADE_REQUIRED, limits)
    assert "or visit" not in msg
