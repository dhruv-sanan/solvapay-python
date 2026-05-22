"""Tests: default_stack() canonical order (HLD V1.4.1 M1)."""

from __future__ import annotations

from solvapay._transport._recipe import default_stack
from solvapay._transport.httpx_transport import AsyncHttpxTransport, HttpxTransport
from solvapay._transport.middleware import (
    AsyncContextPropagatingTransport,
    AsyncIdempotencyHeaderTransport,
    AsyncLoggingTransport,
    AsyncRedactingTransport,
    ContextPropagatingTransport,
    IdempotencyHeaderTransport,
    LoggingTransport,
    RedactingTransport,
)

OPTS = {"api_key": "sk_test", "base_url": "https://api.solvapay.test"}


def test_sync_outermost_is_idempotency_header() -> None:
    sync, _ = default_stack(**OPTS)
    assert isinstance(sync, IdempotencyHeaderTransport)


def test_sync_canonical_order() -> None:
    sync, _ = default_stack(**OPTS)
    assert isinstance(sync, IdempotencyHeaderTransport)
    assert isinstance(sync._inner, LoggingTransport)
    assert isinstance(sync._inner._inner, RedactingTransport)
    assert isinstance(sync._inner._inner._inner, ContextPropagatingTransport)
    assert isinstance(sync._inner._inner._inner._inner, HttpxTransport)


def test_async_canonical_order() -> None:
    _, async_t = default_stack(**OPTS)
    assert isinstance(async_t, AsyncIdempotencyHeaderTransport)
    assert isinstance(async_t._inner, AsyncLoggingTransport)
    assert isinstance(async_t._inner._inner, AsyncRedactingTransport)
    assert isinstance(async_t._inner._inner._inner, AsyncContextPropagatingTransport)
    assert isinstance(async_t._inner._inner._inner._inner, AsyncHttpxTransport)


def test_all_middleware_have_protocol_version_1() -> None:
    sync, async_t = default_stack(**OPTS)
    layer: object = sync
    while hasattr(layer, "_inner"):
        assert getattr(layer, "protocol_version", None) == 1, f"{type(layer)} missing protocol_version=1"
        layer = layer._inner  # type: ignore[union-attr]
