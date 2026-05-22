"""Tests: PayableToolMeta shape + payable_tool decorator (HLD V1.17)."""

from __future__ import annotations

import pytest

from solvapay.paywall.decorators import payable_tool
from solvapay.paywall.meta import PayableToolMeta


def test_meta_version_is_1() -> None:
    meta = PayableToolMeta(product="prd_x")
    assert meta._meta_version == 1


def test_meta_frozen() -> None:
    meta = PayableToolMeta(product="prd_x")
    with pytest.raises((AttributeError, TypeError)):
        meta._meta_version = 2  # type: ignore[misc]


def test_payable_tool_stamps_meta() -> None:
    @payable_tool(product="prd_x")
    def my_fn(*, customer_ref: str) -> str:
        return customer_ref

    assert hasattr(my_fn, "__solvapay_meta__")
    assert my_fn.__solvapay_meta__._meta_version == 1  # type: ignore[attr-defined]
    assert my_fn.__solvapay_meta__.product == "prd_x"  # type: ignore[attr-defined]


def test_payable_tool_preserves_signature() -> None:
    @payable_tool(product="prd_x")
    def compute(*, customer_ref: str, value: int) -> int:
        return value * 2

    assert compute.__name__ == "compute"
    assert compute.__wrapped__.__name__ == "compute"  # type: ignore[attr-defined]


def test_payable_tool_rejects_classmethod() -> None:
    cm: object = classmethod(lambda cls: None)
    with pytest.raises(TypeError, match="classmethod"):
        payable_tool(product="prd_x")(cm)  # type: ignore[arg-type]


def test_payable_tool_rejects_staticmethod() -> None:
    sm: object = staticmethod(lambda: None)
    with pytest.raises(TypeError, match="staticmethod|classmethod"):
        payable_tool(product="prd_x")(sm)  # type: ignore[arg-type]


def test_payable_tool_rejects_bound_method() -> None:
    class _Obj:
        def method(self) -> None: ...

    obj = _Obj()
    with pytest.raises(TypeError, match="bound method"):
        payable_tool(product="prd_x")(obj.method)  # type: ignore[arg-type]
