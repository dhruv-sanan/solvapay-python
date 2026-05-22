"""Tests: Headers case-insensitive wrapper (HLD V1.4 T5)."""

from __future__ import annotations

from solvapay._transport import Headers


def test_get_lowercase() -> None:
    h = Headers({"Content-Type": "application/json"})
    assert h.get("content-type") == "application/json"


def test_get_uppercase() -> None:
    h = Headers({"content-type": "application/json"})
    assert h.get("Content-Type") == "application/json"


def test_getitem() -> None:
    h = Headers({"Authorization": "Bearer sk"})
    assert h["authorization"] == "Bearer sk"
    assert h["Authorization"] == "Bearer sk"


def test_contains() -> None:
    h = Headers({"X-Request-ID": "req_abc"})
    assert "x-request-id" in h
    assert "X-Request-ID" in h
    assert "missing" not in h


def test_items_yields_lowercase_keys() -> None:
    h = Headers({"Content-Type": "json", "Authorization": "Bearer x"})
    keys = {k for k, _ in h.items()}
    assert "content-type" in keys
    assert "authorization" in keys


def test_to_dict_returns_lowercase_keys() -> None:
    h = Headers({"X-Foo": "bar"})
    assert h.to_dict() == {"x-foo": "bar"}


def test_get_default() -> None:
    h = Headers()
    assert h.get("missing") is None
    assert h.get("missing", "fallback") == "fallback"


def test_empty_headers() -> None:
    h = Headers()
    assert h.get("anything") is None
    assert list(h.items()) == []
