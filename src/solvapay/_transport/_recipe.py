"""Canonical transport stack factory (HLD V1.4.1)."""

from __future__ import annotations

import logging
from typing import Any

from solvapay._transport import Timeout
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


def default_stack(
    *,
    api_key: str,
    base_url: str,
    api_version: str | None = None,
    timeout: float | Timeout | None = None,
    logger: logging.Logger | None = None,
) -> tuple[Any, Any]:
    """Build canonical sync + async transport stacks.

    Canonical order (inner → outer, HLD V1.4.1 M1):
      HttpxTransport → ContextPropagating → Redacting → Logging → IdempotencyHeader

    Returns (sync_transport, async_transport).
    """
    t = timeout if timeout is not None else 30.0

    sync: Any = HttpxTransport(
        api_key=api_key,
        base_url=base_url,
        api_version=api_version,
        timeout=t,
        logger=logger,
    )
    sync = ContextPropagatingTransport(sync)
    sync = RedactingTransport(sync)
    sync = LoggingTransport(sync, logger=logger)
    sync = IdempotencyHeaderTransport(sync)

    async_t: Any = AsyncHttpxTransport(
        api_key=api_key,
        base_url=base_url,
        api_version=api_version,
        timeout=t,
        logger=logger,
    )
    async_t = AsyncContextPropagatingTransport(async_t)
    async_t = AsyncRedactingTransport(async_t)
    async_t = AsyncLoggingTransport(async_t, logger=logger)
    async_t = AsyncIdempotencyHeaderTransport(async_t)

    return sync, async_t
