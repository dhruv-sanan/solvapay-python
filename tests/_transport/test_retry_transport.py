"""Tests for RetryTransport — retry policy and safety constraints."""

from __future__ import annotations

import pytest

from solvapay._transport import Headers, RequestSpec, ResponseMetadata, ResponseSpec
from solvapay._transport.middleware import RetryTransport
from solvapay.exceptions import APIConnectionError, AuthenticationError


def _ok_response() -> ResponseSpec:
    return ResponseSpec(body={}, metadata=ResponseMetadata(200, Headers({}), 0))


class _CountingTransport:
    def __init__(self, *, fail_times: int = 0, exc: type[Exception] = APIConnectionError) -> None:
        self.calls = 0
        self._fail_times = fail_times
        self._exc = exc

    def send(self, spec: RequestSpec) -> ResponseSpec:
        self.calls += 1
        if self.calls <= self._fail_times:
            if self._exc is AuthenticationError:
                raise AuthenticationError(401, "Unauthorized")
            raise self._exc("simulated failure")  # type: ignore[call-arg]
        return _ok_response()

    def close(self) -> None:
        pass


def _spec(method: str = "GET", idempotency_key: str | None = None) -> RequestSpec:
    headers: dict[str, str] = {}
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    return RequestSpec(method=method, url="/test", headers=Headers(headers), json=None)


def test_retries_connection_error_then_succeeds() -> None:
    inner = _CountingTransport(fail_times=2, exc=APIConnectionError)
    transport = RetryTransport(inner, max_attempts=3)
    resp = transport.send(_spec("GET"))
    assert resp.metadata.status_code == 200
    assert inner.calls == 3


def test_no_retry_on_auth_error() -> None:
    inner = _CountingTransport(fail_times=3, exc=AuthenticationError)
    transport = RetryTransport(inner, max_attempts=3)
    with pytest.raises(AuthenticationError):
        transport.send(_spec("GET"))
    assert inner.calls == 1


def test_post_without_idempotency_key_not_retried() -> None:
    inner = _CountingTransport(fail_times=3, exc=APIConnectionError)
    transport = RetryTransport(inner, max_attempts=3)
    with pytest.raises(APIConnectionError):
        transport.send(_spec("POST", idempotency_key=None))
    assert inner.calls == 1


def test_post_with_idempotency_key_is_retried() -> None:
    inner = _CountingTransport(fail_times=2, exc=APIConnectionError)
    transport = RetryTransport(inner, max_attempts=3)
    resp = transport.send(_spec("POST", idempotency_key="idem_123"))
    assert resp.metadata.status_code == 200
    assert inner.calls == 3


def test_exceeds_max_attempts_raises_last_exception() -> None:
    inner = _CountingTransport(fail_times=10, exc=APIConnectionError)
    transport = RetryTransport(inner, max_attempts=3)
    with pytest.raises(APIConnectionError):
        transport.send(_spec("GET"))
    assert inner.calls == 3
