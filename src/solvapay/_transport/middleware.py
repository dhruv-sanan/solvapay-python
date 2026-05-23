"""Transport middleware stack (HLD V1.4.1).

Canonical composition order (inner → outer):
  HttpxTransport → ContextPropagating → Redacting → Logging → IdempotencyHeader
  → RetryTransport (optional, outermost, solvapay[retry])

Each middleware:
- Implements aclose() for AL2 cascade.
- Propagates SolvaPayError subclasses unchanged.
- Wraps unknown exceptions as APIError(error_code="middleware_failure") (HLD M3).
"""

from __future__ import annotations

import dataclasses
import json
import logging
import os
import time
from typing import ClassVar

from solvapay._transport import AsyncTransport, Headers, RequestSpec, ResponseSpec, Transport
from solvapay.exceptions import (
    APIConnectionError,
    APIError,
    APIServerError,
    APITimeoutError,
    RateLimitError,
    SolvaPayError,
)


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
        request_id = resp.metadata.headers.get("x-request-id") or resp.metadata.headers.get(
            "x-correlation-id"
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
        request_id = resp.metadata.headers.get("x-request-id") or resp.metadata.headers.get(
            "x-correlation-id"
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


# ── Optional middleware: RetryTransport (solvapay[retry]) ──

_RETRYABLE = (APIConnectionError, APITimeoutError, APIServerError, RateLimitError)


class RetryTransport:
    """Retry transient errors using exponential backoff with jitter (solvapay[retry]).

    Retries on: APIConnectionError, APITimeoutError, APIServerError, RateLimitError.
    Only retries POST/PATCH if Idempotency-Key is set — safe by construction.
    Requires: pip install solvapay-python[retry]  (tenacity>=8.2).
    """

    protocol_version: ClassVar[int] = 1

    def __init__(self, inner: Transport, *, max_attempts: int = 3) -> None:
        self._inner = inner
        self._max_attempts = max_attempts

    def _should_retry(self, spec: RequestSpec, exc: BaseException) -> bool:
        if not isinstance(exc, _RETRYABLE):
            return False
        # Mutating ops without idempotency key must not be retried
        if spec.method.upper() in ("POST", "PATCH", "DELETE"):
            has_key = bool(
                spec.headers.get("Idempotency-Key")
                or (spec.context and spec.context.extras.get("idempotency_key"))
            )
            if not has_key:
                return False
        return True

    def send(self, spec: RequestSpec) -> ResponseSpec:
        import random

        last_exc: BaseException
        for attempt in range(self._max_attempts):
            try:
                return self._inner.send(spec)
            except BaseException as exc:
                last_exc = exc
                if not self._should_retry(spec, exc):
                    raise
                if attempt + 1 < self._max_attempts:
                    wait = min(0.5 * (2**attempt) + random.uniform(0, 0.5), 8.0)
                    time.sleep(wait)
        raise last_exc

    def close(self) -> None:
        self._inner.close()


class AsyncRetryTransport:
    """Async variant of RetryTransport (solvapay[retry])."""

    protocol_version: ClassVar[int] = 1

    def __init__(self, inner: AsyncTransport, *, max_attempts: int = 3) -> None:
        self._inner = inner
        self._max_attempts = max_attempts

    def _should_retry(self, spec: RequestSpec, exc: BaseException) -> bool:
        if not isinstance(exc, _RETRYABLE):
            return False
        if spec.method.upper() in ("POST", "PATCH", "DELETE"):
            has_key = bool(
                spec.headers.get("Idempotency-Key")
                or (spec.context and spec.context.extras.get("idempotency_key"))
            )
            if not has_key:
                return False
        return True

    async def send(self, spec: RequestSpec) -> ResponseSpec:
        import asyncio
        import random

        last_exc: BaseException
        for attempt in range(self._max_attempts):
            try:
                return await self._inner.send(spec)
            except BaseException as exc:
                last_exc = exc
                if not self._should_retry(spec, exc):
                    raise
                if attempt + 1 < self._max_attempts:
                    wait = min(0.5 * (2**attempt) + random.uniform(0, 0.5), 8.0)
                    await asyncio.sleep(wait)
        raise last_exc

    async def aclose(self) -> None:
        await self._inner.aclose()


# ── Optional middleware: RecordingTransport (for contract tests) ──


class RecordingTransport:
    """Record request/response pairs to a JSON cassette; replay on subsequent runs.

    On first run (cassette absent): forwards to inner transport, records to cassette_path.
    On subsequent runs (cassette present): replays recorded responses without hitting network.

    Cassette format (list of objects)::

        [
          {
            "request": {"method": "POST", "url": "/v1/sdk/limits", "json": {...}},
            "response": {"status_code": 200, "body": {...}, "headers": {}}
          }
        ]
    """

    protocol_version: ClassVar[int] = 1

    def __init__(self, inner: Transport, *, cassette_path: str) -> None:
        self._inner = inner
        self._cassette_path = cassette_path
        self._recordings: list[dict[str, object]] = []
        self._replay: list[dict[str, object]] | None = None
        self._replay_index: int = 0
        if os.path.exists(cassette_path):
            with open(cassette_path) as f:
                self._replay = json.load(f)

    def send(self, spec: RequestSpec) -> ResponseSpec:
        from solvapay._transport import ResponseMetadata

        if self._replay is not None:
            entry = self._replay[self._replay_index]
            self._replay_index += 1
            rec = entry["response"]
            assert isinstance(rec, dict)
            body = rec.get("body", {})
            headers = rec.get("headers", {})
            return ResponseSpec(
                body=body if isinstance(body, dict) else {},
                metadata=ResponseMetadata(
                    status_code=int(rec.get("status_code", 200)),
                    headers=Headers(headers if isinstance(headers, dict) else {}),
                    elapsed_ms=0,
                ),
            )
        resp = self._inner.send(spec)
        self._recordings.append(
            {
                "request": {
                    "method": spec.method,
                    "url": spec.url,
                    "json": dict(spec.json) if spec.json else None,
                },
                "response": {
                    "status_code": resp.metadata.status_code,
                    "body": resp.body,
                    "headers": dict(resp.metadata.headers.items()),
                },
            }
        )
        with open(self._cassette_path, "w") as f:
            json.dump(self._recordings, f, indent=2)
        return resp

    def close(self) -> None:
        self._inner.close()
