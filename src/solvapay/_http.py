"""Internal HTTP transport. Not part of public API."""
from __future__ import annotations

from typing import Any

import httpx

from solvapay.exceptions import SolvaPayAPIError


class HttpClient:
    """Thin httpx wrapper. One method: request(). No retries in v0.1."""

    def __init__(self, *, api_key: str, base_url: str, timeout: float = 30.0) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "solvapay-python/0.1.0",
            },
            timeout=timeout,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        headers: dict[str, str] = {}
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key
        response = self._client.request(method, path, json=json, params=params, headers=headers)
        if not response.is_success:
            raise SolvaPayAPIError(response.status_code, response.text)
        if response.status_code == 204 or not response.content:
            return {}
        return response.json()  # type: ignore[no-any-return]
