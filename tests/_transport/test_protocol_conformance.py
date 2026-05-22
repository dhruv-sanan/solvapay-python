"""Tests: Transport Protocol conformance (HLD V1.4 T6)."""

from __future__ import annotations

from solvapay._transport import AsyncTransport, Transport
from solvapay._transport.httpx_transport import AsyncHttpxTransport, HttpxTransport


def _make_sync() -> HttpxTransport:
    return HttpxTransport(api_key="sk_test", base_url="https://api.solvapay.test")


def _make_async() -> AsyncHttpxTransport:
    return AsyncHttpxTransport(api_key="sk_test", base_url="https://api.solvapay.test")


def test_httpx_transport_protocol_version() -> None:
    assert HttpxTransport.protocol_version == 1


def test_async_httpx_transport_protocol_version() -> None:
    assert AsyncHttpxTransport.protocol_version == 1


def test_httpx_transport_isinstance_transport() -> None:
    t = _make_sync()
    assert isinstance(t, Transport)
    t.close()


def test_async_httpx_transport_isinstance_async_transport() -> None:
    t = _make_async()
    assert isinstance(t, AsyncTransport)


def test_transport_has_send_and_close() -> None:
    t = _make_sync()
    assert callable(t.send)
    assert callable(t.close)
    t.close()


def test_async_transport_has_send_and_aclose() -> None:
    t = _make_async()
    assert callable(t.send)
    assert callable(t.aclose)
