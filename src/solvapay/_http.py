"""Internal HTTP transport. Not part of public API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

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


@dataclass(frozen=True)
class _RequestSpec:
    method: str
    path: str
    json: dict[str, Any] | None = None
    params: dict[str, Any] | None = None
    idempotency_key: str | None = None

    def headers(self) -> dict[str, str]:
        return {"Idempotency-Key": self.idempotency_key} if self.idempotency_key else {}


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


class HttpClient:
    def __init__(self, *, api_key: str, base_url: str, timeout: float = 30.0) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "solvapay-python/0.7.0",
            },
            timeout=timeout,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def send(self, spec: _RequestSpec) -> dict[str, Any]:
        try:
            return _handle(
                self._client.request(
                    spec.method,
                    spec.path,
                    json=spec.json,
                    params=spec.params,
                    headers=spec.headers(),
                )
            )
        except httpx.TimeoutException as exc:
            raise APITimeoutError(str(exc)) from exc
        except (httpx.ConnectError, httpx.ReadError) as exc:
            raise APIConnectionError(str(exc)) from exc

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
    def __init__(self, *, api_key: str, base_url: str, timeout: float = 30.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "solvapay-python/0.7.0",
            },
            timeout=timeout,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AsyncHttpClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def send(self, spec: _RequestSpec) -> dict[str, Any]:
        try:
            return _handle(
                await self._client.request(
                    spec.method,
                    spec.path,
                    json=spec.json,
                    params=spec.params,
                    headers=spec.headers(),
                )
            )
        except httpx.TimeoutException as exc:
            raise APITimeoutError(str(exc)) from exc
        except (httpx.ConnectError, httpx.ReadError) as exc:
            raise APIConnectionError(str(exc)) from exc
