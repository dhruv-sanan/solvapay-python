"""Internal HTTP transport. Not part of public API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from solvapay.exceptions import SolvaPayAPIError


@dataclass(frozen=True)
class _RequestSpec:
    method: str
    path: str
    json: dict[str, Any] | None = None
    params: dict[str, Any] | None = None
    idempotency_key: str | None = None

    def headers(self) -> dict[str, str]:
        return {"Idempotency-Key": self.idempotency_key} if self.idempotency_key else {}


def _handle(response: httpx.Response) -> dict[str, Any]:
    if not response.is_success:
        raise SolvaPayAPIError(response.status_code, response.text)
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
        return _handle(
            self._client.request(
                spec.method,
                spec.path,
                json=spec.json,
                params=spec.params,
                headers=spec.headers(),
            )
        )

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
        return _handle(
            await self._client.request(
                spec.method,
                spec.path,
                json=spec.json,
                params=spec.params,
                headers=spec.headers(),
            )
        )
