"""Tests: every OpSpec in REGISTRY has the correct retry_safety value (HLD OR1)."""

from __future__ import annotations

import pytest

from solvapay.operations._registry import REGISTRY, RetrySafety

# Expected retry_safety per operation
_EXPECTED: dict[str, RetrySafety] = {
    "customers.ensure": RetrySafety.WITH_KEY,
    "customers.get": RetrySafety.ALWAYS,
    "customers.update": RetrySafety.ALWAYS,
    "customers.balance": RetrySafety.ALWAYS,
    "checkout.create_session": RetrySafety.WITH_KEY,
    "limits.check": RetrySafety.ALWAYS,
    "purchases.cancel": RetrySafety.WITH_KEY,
    "purchases.reactivate": RetrySafety.WITH_KEY,
    "usage.track": RetrySafety.NEVER,
    "products.list": RetrySafety.ALWAYS,
    "products.get": RetrySafety.ALWAYS,
    "products.create": RetrySafety.WITH_KEY,
    "products.delete": RetrySafety.ALWAYS,
    "products.clone": RetrySafety.WITH_KEY,
    "plans.list": RetrySafety.ALWAYS,
    "plans.create": RetrySafety.WITH_KEY,
    "plans.update": RetrySafety.ALWAYS,
    "plans.delete": RetrySafety.ALWAYS,
    "merchant.get": RetrySafety.ALWAYS,
    "platform.get_config": RetrySafety.ALWAYS,
}


@pytest.mark.parametrize("op_name,expected", _EXPECTED.items())
def test_op_retry_safety(op_name: str, expected: RetrySafety) -> None:
    spec = REGISTRY[op_name]
    assert spec.retry_safety == expected, f"{op_name}: expected {expected}, got {spec.retry_safety}"


def test_registry_covers_all_expected_ops() -> None:
    for op_name in _EXPECTED:
        assert op_name in REGISTRY, f"Missing from REGISTRY: {op_name}"


def test_all_registry_ops_have_retry_safety() -> None:
    for name, spec in REGISTRY.items():
        assert isinstance(spec.retry_safety, RetrySafety), f"{name} missing retry_safety"


def test_usage_track_is_never() -> None:
    assert REGISTRY["usage.track"].retry_safety == RetrySafety.NEVER


def test_gets_are_always() -> None:
    get_ops = [name for name, spec in REGISTRY.items() if spec.method == "GET"]
    for name in get_ops:
        assert REGISTRY[name].retry_safety == RetrySafety.ALWAYS, f"GET op {name} should be ALWAYS"
