"""Tests: aclose() cascades through all middleware (HLD V1.15 AL2)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from solvapay._transport import Headers, RequestSpec, ResponseMetadata, ResponseSpec
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


def _mock_sync_inner() -> MagicMock:
    inner = MagicMock()
    inner.protocol_version = 1
    inner.send.return_value = ResponseSpec(
        body={},
        metadata=ResponseMetadata(
            status_code=200,
            headers=Headers(),
            elapsed_ms=1,
        ),
    )
    return inner


def _mock_async_inner() -> MagicMock:
    inner = MagicMock()
    inner.protocol_version = 1
    inner.aclose = AsyncMock()
    return inner


def test_redacting_transport_close_delegates() -> None:
    inner = _mock_sync_inner()
    t = RedactingTransport(inner)
    t.close()
    inner.close.assert_called_once()


def test_logging_transport_close_delegates() -> None:
    inner = _mock_sync_inner()
    t = LoggingTransport(inner)
    t.close()
    inner.close.assert_called_once()


def test_idempotency_transport_close_delegates() -> None:
    inner = _mock_sync_inner()
    t = IdempotencyHeaderTransport(inner)
    t.close()
    inner.close.assert_called_once()


def test_context_propagating_close_delegates() -> None:
    inner = _mock_sync_inner()
    t = ContextPropagatingTransport(inner)
    t.close()
    inner.close.assert_called_once()


@pytest.mark.asyncio
async def test_async_redacting_aclose_cascades() -> None:
    inner = _mock_async_inner()
    t = AsyncRedactingTransport(inner)
    await t.aclose()
    inner.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_logging_aclose_cascades() -> None:
    inner = _mock_async_inner()
    t = AsyncLoggingTransport(inner)
    await t.aclose()
    inner.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_idempotency_aclose_cascades() -> None:
    inner = _mock_async_inner()
    t = AsyncIdempotencyHeaderTransport(inner)
    await t.aclose()
    inner.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_context_aclose_cascades() -> None:
    inner = _mock_async_inner()
    t = AsyncContextPropagatingTransport(inner)
    await t.aclose()
    inner.aclose.assert_awaited_once()
