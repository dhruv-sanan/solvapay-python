"""Tests: non-SDK exceptions wrapped as APIError("middleware_failure") (HLD M3)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from solvapay._transport import Headers, RequestSpec, ResponseMetadata, ResponseSpec
from solvapay._transport.middleware import (
    ContextPropagatingTransport,
    IdempotencyHeaderTransport,
    LoggingTransport,
    RedactingTransport,
)
from solvapay.exceptions import APIError, AuthenticationError


def _spec() -> RequestSpec:
    return RequestSpec(method="GET", url="/v1/sdk/test", headers=Headers(), json=None)


def _middleware_raising(cls, exc: Exception) -> object:
    inner = MagicMock()
    inner.protocol_version = 1
    inner.send.side_effect = exc
    inner.close = MagicMock()
    return cls(inner)


def test_redacting_wraps_non_sdk_exception() -> None:
    t = _middleware_raising(RedactingTransport, RuntimeError("boom"))
    with pytest.raises(APIError) as exc_info:
        t.send(_spec())  # type: ignore[arg-type]
    assert exc_info.value.error_code == "middleware_failure"


def test_logging_wraps_non_sdk_exception() -> None:
    t = _middleware_raising(LoggingTransport, ValueError("oops"))
    with pytest.raises(APIError) as exc_info:
        t.send(_spec())  # type: ignore[arg-type]
    assert exc_info.value.error_code == "middleware_failure"


def test_idempotency_wraps_non_sdk_exception() -> None:
    t = _middleware_raising(IdempotencyHeaderTransport, OSError("network"))
    with pytest.raises(APIError) as exc_info:
        t.send(_spec())  # type: ignore[arg-type]
    assert exc_info.value.error_code == "middleware_failure"


def test_context_wraps_non_sdk_exception() -> None:
    t = _middleware_raising(ContextPropagatingTransport, KeyError("key"))
    with pytest.raises(APIError) as exc_info:
        t.send(_spec())  # type: ignore[arg-type]
    assert exc_info.value.error_code == "middleware_failure"


def test_sdk_exceptions_propagate_unchanged() -> None:
    inner = MagicMock()
    inner.protocol_version = 1
    inner.send.side_effect = AuthenticationError(401, "unauthorized")
    inner.close = MagicMock()
    t = RedactingTransport(inner)
    with pytest.raises(AuthenticationError):
        t.send(_spec())  # type: ignore[arg-type]
