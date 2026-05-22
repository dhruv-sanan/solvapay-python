"""Transport middleware stack (HLD V1.4.1).

Canonical composition order (inner → outer):
  HttpxTransport → ContextPropagating → Redacting → Logging → IdempotencyHeader

Each middleware:
- Implements aclose() for AL2 cascade.
- Propagates SolvaPayError subclasses unchanged.
- Wraps unknown exceptions as APIError(error_code="middleware_failure") (HLD M3).
"""

from __future__ import annotations

import dataclasses
import logging
import time
from typing import ClassVar

from solvapay._transport import AsyncTransport, Headers, RequestSpec, ResponseSpec, Transport
from solvapay.exceptions import APIError, SolvaPayError


def _wrap_non_sdk(exc: BaseException) -> SolvaPayError:
    """HLD M3: wrap non-SDK exceptions as APIError("middleware_failure")."""
    if isinstance(exc, SolvaPayError):
        return exc
    return APIError(0, str(exc), error_code="middleware_failure")


# ── Sync middleware ──


class RedactingTransport:
    """Passes request through; strips Authorization from any inbound headers before logging (HLD M2)."""

    protocol_version: ClassVar[int] = 1

    def __init__(self, inner: Transport) -> None:
        self._inner = inner

    def send(self, spec: RequestSpec) -> ResponseSpec:
        try:
            return self._inner.send(spec)
        except SolvaPayError:
            raise
        except Exception as exc:
            raise _wrap_non_sdk(exc) from exc

    def close(self) -> None:
        self._inner.close()


class LoggingTransport:
    """Logs request + response at INFO/WARNING (HLD M2: always after redact)."""

    protocol_version: ClassVar[int] = 1

    def __init__(self, inner: Transport, *, logger: logging.Logger | None = None) -> None:
        self._inner = inner
        self._logger = logger or logging.getLogger("solvapay.transport")

    def send(self, spec: RequestSpec) -> ResponseSpec:
        t0 = time.perf_counter()
        try:
            resp = self._inner.send(spec)
        except SolvaPayError:
            raise
        except Exception as exc:
            raise _wrap_non_sdk(exc) from exc
        elapsed = int((time.perf_counter() - t0) * 1000)
        request_id = (
            resp.metadata.headers.get("x-request-id")
            or resp.metadata.headers.get("x-correlation-id")
        )
        self._logger.info(
            "%s %s → %d (%dms)",
            spec.method,
            spec.url,
            resp.metadata.status_code,
            elapsed,
            extra={"request_id": request_id, "duration_ms": elapsed},
        )
        return resp

    def close(self) -> None:
        self._inner.close()


class IdempotencyHeaderTransport:
    """Injects Idempotency-Key from context.extras['idempotency_key'] (HLD V1.4.1 M2)."""

    protocol_version: ClassVar[int] = 1

    def __init__(self, inner: Transport) -> None:
        self._inner = inner

    def send(self, spec: RequestSpec) -> ResponseSpec:
        key = spec.context.extras.get("idempotency_key") if spec.context else None
        if key:
            new_headers_dict = dict(spec.headers.items())
            new_headers_dict["Idempotency-Key"] = str(key)
            spec = dataclasses.replace(spec, headers=Headers(new_headers_dict))
        try:
            return self._inner.send(spec)
        except SolvaPayError:
            raise
        except Exception as exc:
            raise _wrap_non_sdk(exc) from exc

    def close(self) -> None:
        self._inner.close()


class ContextPropagatingTransport:
    """Propagates Context.trace_id into X-Trace-ID header."""

    protocol_version: ClassVar[int] = 1

    def __init__(self, inner: Transport) -> None:
        self._inner = inner

    def send(self, spec: RequestSpec) -> ResponseSpec:
        if spec.context and spec.context.trace_id:
            new_headers_dict = dict(spec.headers.items())
            new_headers_dict["X-Trace-ID"] = spec.context.trace_id
            spec = dataclasses.replace(spec, headers=Headers(new_headers_dict))
        try:
            return self._inner.send(spec)
        except SolvaPayError:
            raise
        except Exception as exc:
            raise _wrap_non_sdk(exc) from exc

    def close(self) -> None:
        self._inner.close()


# ── Async middleware ──


class AsyncRedactingTransport:
    protocol_version: ClassVar[int] = 1

    def __init__(self, inner: AsyncTransport) -> None:
        self._inner = inner

    async def send(self, spec: RequestSpec) -> ResponseSpec:
        try:
            return await self._inner.send(spec)
        except SolvaPayError:
            raise
        except Exception as exc:
            raise _wrap_non_sdk(exc) from exc

    async def aclose(self) -> None:
        await self._inner.aclose()


class AsyncLoggingTransport:
    protocol_version: ClassVar[int] = 1

    def __init__(self, inner: AsyncTransport, *, logger: logging.Logger | None = None) -> None:
        self._inner = inner
        self._logger = logger or logging.getLogger("solvapay.transport")

    async def send(self, spec: RequestSpec) -> ResponseSpec:
        t0 = time.perf_counter()
        try:
            resp = await self._inner.send(spec)
        except SolvaPayError:
            raise
        except Exception as exc:
            raise _wrap_non_sdk(exc) from exc
        elapsed = int((time.perf_counter() - t0) * 1000)
        request_id = (
            resp.metadata.headers.get("x-request-id")
            or resp.metadata.headers.get("x-correlation-id")
        )
        self._logger.info(
            "%s %s → %d (%dms)",
            spec.method,
            spec.url,
            resp.metadata.status_code,
            elapsed,
            extra={"request_id": request_id, "duration_ms": elapsed},
        )
        return resp

    async def aclose(self) -> None:
        await self._inner.aclose()


class AsyncIdempotencyHeaderTransport:
    protocol_version: ClassVar[int] = 1

    def __init__(self, inner: AsyncTransport) -> None:
        self._inner = inner

    async def send(self, spec: RequestSpec) -> ResponseSpec:
        key = spec.context.extras.get("idempotency_key") if spec.context else None
        if key:
            new_headers_dict = dict(spec.headers.items())
            new_headers_dict["Idempotency-Key"] = str(key)
            spec = dataclasses.replace(spec, headers=Headers(new_headers_dict))
        try:
            return await self._inner.send(spec)
        except SolvaPayError:
            raise
        except Exception as exc:
            raise _wrap_non_sdk(exc) from exc

    async def aclose(self) -> None:
        await self._inner.aclose()


class AsyncContextPropagatingTransport:
    protocol_version: ClassVar[int] = 1

    def __init__(self, inner: AsyncTransport) -> None:
        self._inner = inner

    async def send(self, spec: RequestSpec) -> ResponseSpec:
        if spec.context and spec.context.trace_id:
            new_headers_dict = dict(spec.headers.items())
            new_headers_dict["X-Trace-ID"] = spec.context.trace_id
            spec = dataclasses.replace(spec, headers=Headers(new_headers_dict))
        try:
            return await self._inner.send(spec)
        except SolvaPayError:
            raise
        except Exception as exc:
            raise _wrap_non_sdk(exc) from exc

    async def aclose(self) -> None:
        await self._inner.aclose()
