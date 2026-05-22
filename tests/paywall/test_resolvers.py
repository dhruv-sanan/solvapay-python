"""Tests: built-in CustomerRef resolvers."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from solvapay.paywall.resolvers import KwargsResolver, PositionalResolver, PydanticBodyResolver


class _Body(BaseModel):
    customer_ref: str
    other: str = "x"


def test_kwargs_resolver_basic() -> None:
    r = KwargsResolver("customer_ref")
    assert r.resolve(customer_ref="cus_abc") == "cus_abc"


def test_kwargs_resolver_missing_raises() -> None:
    r = KwargsResolver("customer_ref")
    with pytest.raises(ValueError, match="customer_ref"):
        r.resolve(other="x")


def test_positional_resolver_basic() -> None:
    r = PositionalResolver(0)
    assert r.resolve("cus_abc", "other") == "cus_abc"


def test_positional_resolver_out_of_range() -> None:
    r = PositionalResolver(5)
    with pytest.raises(ValueError, match="index 5"):
        r.resolve("only_one")


def test_pydantic_body_resolver_basic() -> None:
    r = PydanticBodyResolver(body_arg="body", field="customer_ref")
    body = _Body(customer_ref="cus_xyz")
    assert r.resolve(body=body) == "cus_xyz"


def test_pydantic_body_resolver_missing_kwarg() -> None:
    r = PydanticBodyResolver(body_arg="req")
    with pytest.raises(ValueError, match="'req' not found"):
        r.resolve(body=_Body(customer_ref="cus_abc"))
