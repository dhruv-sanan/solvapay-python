"""Internal HTTP transport (re-export shim). Use solvapay._transport directly."""

from __future__ import annotations

from solvapay._transport.httpx_transport import (
    AsyncHttpClient,
    HttpClient,
    _handle,
    _log_response,
    _parse_error,
    _RequestSpec,
)

__all__ = [
    "AsyncHttpClient",
    "HttpClient",
    "_RequestSpec",
    "_handle",
    "_log_response",
    "_parse_error",
]
