"""Default httpx-backed Transport implementation + backward-compat HttpClient wrappers."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, ClassVar

import httpx

from solvapay._transport import (
    Headers,
    RequestSpec,
    ResponseMetadata,
    ResponseSpec,
    Timeout,
)
from solvapay.exceptions import (
    APIConnectionError,
    APIError,
    APIServerError,
    APITimeoutError,
    AuthenticationError,
    InvalidRequestError,
    NotFoundError,
    PermissionError,
    RateLimitError,
)

_logger = logging.getLogger("solvapay.http")

_VERSION = "0.8.0"  # keep in sync with __version__


# ── Legacy _RequestSpec — kept for HttpClient / AsyncHttpClient backward-compat ──


@dataclass(frozen=True)
class _RequestSpec:
    method: str
    path: str
    json: dict[str, Any] | None = None
    params: dict[str, Any] | None = None
    idempotency_key: str | None = None

    def headers(self) -> dict[str, str]:
        return {"Idempotency-Key": self.idempotency_key} if self.idempotency_key else {}


# ── Shared error mapping ──


def _parse_error(response: httpx.Response) -> APIError:
    request_id = response.headers.get("x-request-id") or response.headers.get("x-correlation-id")
    error_code: str | None = None
    error_message: str | None = None
    try:
        payload = response.json()
        if isinstance(payload, dict):
            err = payload.get("error", payload)
            if isinstance(err, dict):
                code = err.get("code")
                msg = err.get("message")
                if isinstance(code, str):
                    error_code = code
                if isinstance(msg, str):
                    error_message = msg
    except Exception:
        pass

    status = response.status_code
    body = response.text

    if status == 401:
        return AuthenticationError(
            status, body, request_id=request_id, error_code=error_code, error_message=error_message
        )
    if status == 403:
        return PermissionError(
            status, body, request_id=request_id, error_code=error_code, error_message=error_message
        )
    if status == 404:
        return NotFoundError(
            status, body, request_id=request_id, error_code=error_code, error_message=error_message
        )
    if status == 429:
        return RateLimitError(
            status,
            body,
            request_id=request_id,
            error_code=error_code,
            error_message=error_message,
            retry_after=response.headers.get("Retry-After"),
        )
    if 400 <= status < 500:
        return InvalidRequestError(
            status, body, request_id=request_id, error_code=error_code, error_message=error_message
        )
    return APIServerError(
        status, body, request_id=request_id, error_code=error_code, error_message=error_message
    )


def _handle(response: httpx.Response) -> dict[str, Any]:
    if not response.is_success:
        raise _parse_error(response)
    if response.status_code == 204 or not response.content:
        return {}
    return response.json()  # type: ignore[no-any-return]


def _log_response(
    logger: logging.Logger,
    method: str,
    path: str,
    response: httpx.Response,
    duration_ms: int,
) -> None:
    request_id = response.headers.get("x-request-id") or response.headers.get("x-correlation-id")
    extra: dict[str, object] = {"request_id": request_id, "duration_ms": duration_ms}
    if response.is_success:
        logger.info(
            "%s %s → %d (%dms)",
            method,
            path,
            response.status_code,
            duration_ms,
            extra=extra,
        )
    else:
        logger.warning(
            "%s %s → %d (%dms)",
            method,
            path,
            response.status_code,
            duration_ms,
            extra={**extra, "body_excerpt": response.text[:200]},
        )


def _make_httpx_timeout(timeout: float | Timeout) -> httpx.Timeout:
    if isinstance(timeout, Timeout):
        return httpx.Timeout(
            connect=timeout.connect,
            read=timeout.read,
            write=timeout.write,
            pool=timeout.pool,
        )
    return httpx.Timeout(timeout)


# ── V1 Transport Protocol implementation ──


class HttpxTransport:
    """Default synchronous Transport implementation (HLD V1.4).

    protocol_version = 1 (HLD T6).
    Logs to 'solvapay.http'. Never logs Authorization header.
    """

    protocol_version: ClassVar[int] = 1

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout: float | Timeout = 30.0,
        logger: logging.Logger | None = None,
        api_version: str | None = None,
    ) -> None:
        self._logger = logger or _logger
        self._api_version = api_version
        headers: dict[str, str] = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"solvapay-python/{_VERSION}",
        }
        if api_version:
            headers["Solvapay-Version"] = api_version
        self._client = httpx.Client(
            base_url=base_url,
            headers=headers,
            timeout=_make_httpx_timeout(timeout),
        )

    def send(self, spec: RequestSpec) -> ResponseSpec:
        t0 = time.perf_counter()
        extra_headers = dict(spec.headers.items()) if spec.headers else {}
        try:
            response = self._client.request(
                spec.method,
                spec.url,
                json=dict(spec.json) if spec.json is not None else None,
                params=spec.params,
                headers=extra_headers,
            )
        except httpx.TimeoutException as exc:
            raise APITimeoutError(str(exc)) from exc
        except (httpx.ConnectError, httpx.ReadError) as exc:
            raise APIConnectionError(str(exc)) from exc

        elapsed = int((time.perf_counter() - t0) * 1000)
        _log_response(self._logger, spec.method, spec.url, response, elapsed)

        if not response.is_success:
            raise _parse_error(response)
        if response.status_code == 204 or not response.content:
            body: dict[str, Any] = {}
        else:
            body = response.json()

        return ResponseSpec(
            body=body,
            metadata=ResponseMetadata(
                status_code=response.status_code,
                headers=Headers(dict(response.headers)),
                elapsed_ms=elapsed,
            ),
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> HttpxTransport:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class AsyncHttpxTransport:
    """Default async Transport implementation (HLD V1.4)."""

    protocol_version: ClassVar[int] = 1

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout: float | Timeout = 30.0,
        logger: logging.Logger | None = None,
        api_version: str | None = None,
    ) -> None:
        self._logger = logger or _logger
        self._api_version = api_version
        headers: dict[str, str] = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"solvapay-python/{_VERSION}",
        }
        if api_version:
            headers["Solvapay-Version"] = api_version
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=_make_httpx_timeout(timeout),
        )

    async def send(self, spec: RequestSpec) -> ResponseSpec:
        t0 = time.perf_counter()
        extra_headers = dict(spec.headers.items()) if spec.headers else {}
        try:
            response = await self._client.request(
                spec.method,
                spec.url,
                json=dict(spec.json) if spec.json is not None else None,
                params=spec.params,
                headers=extra_headers,
            )
        except httpx.TimeoutException as exc:
            raise APITimeoutError(str(exc)) from exc
        except (httpx.ConnectError, httpx.ReadError) as exc:
            raise APIConnectionError(str(exc)) from exc

        elapsed = int((time.perf_counter() - t0) * 1000)
        _log_response(self._logger, spec.method, spec.url, response, elapsed)

        if not response.is_success:
            raise _parse_error(response)
        if response.status_code == 204 or not response.content:
            body: dict[str, Any] = {}
        else:
            body = response.json()

        return ResponseSpec(
            body=body,
            metadata=ResponseMetadata(
                status_code=response.status_code,
                headers=Headers(dict(response.headers)),
                elapsed_ms=elapsed,
            ),
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AsyncHttpxTransport:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()


# ── Backward-compat wrappers (used by client.py / _async_client.py) ──


class HttpClient:
    """Backward-compat sync client. Wraps HttpxTransport; provides old dict-returning interface."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout: float = 30.0,
        logger: logging.Logger | None = None,
        api_version: str | None = None,
    ) -> None:
        self._logger = logger or _logger
        self._transport = HttpxTransport(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            logger=logger,
            api_version=api_version,
        )

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def send(self, spec: _RequestSpec) -> dict[str, Any]:
        new_spec = RequestSpec(
            method=spec.method,
            url=spec.path,
            headers=Headers(spec.headers()),
            json=spec.json,
            params=spec.params,
        )
        return self._transport.send(new_spec).body

    def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        return self.send(_RequestSpec(method, path, json, params, idempotency_key))


class AsyncHttpClient:
    """Backward-compat async client. Wraps AsyncHttpxTransport."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout: float = 30.0,
        logger: logging.Logger | None = None,
        api_version: str | None = None,
    ) -> None:
        self._logger = logger or _logger
        self._transport = AsyncHttpxTransport(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            logger=logger,
            api_version=api_version,
        )

    async def aclose(self) -> None:
        await self._transport.aclose()

    async def __aenter__(self) -> AsyncHttpClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def send(self, spec: _RequestSpec) -> dict[str, Any]:
        new_spec = RequestSpec(
            method=spec.method,
            url=spec.path,
            headers=Headers(spec.headers()),
            json=spec.json,
            params=spec.params,
        )
        return (await self._transport.send(new_spec)).body
