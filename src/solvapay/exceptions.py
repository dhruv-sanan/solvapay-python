"""Exception hierarchy for SolvaPay SDK."""

from __future__ import annotations


class SolvaPayError(Exception):
    """Base exception for all SolvaPay SDK errors."""


class APIError(SolvaPayError):
    """Raised when the SolvaPay API returns a non-2xx response."""

    def __init__(
        self,
        status_code: int,
        body: str,
        *,
        request_id: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        message: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.body = body
        self.request_id = request_id
        self.error_code = error_code
        self.error_message = error_message
        super().__init__(message or f"SolvaPay API error {status_code}: {body}")


class AuthenticationError(APIError):
    """401 — invalid or missing API key."""


class PermissionError(APIError):  # shadows built-in; intentional in SDK module namespace
    """403 — insufficient permissions for this operation."""


class NotFoundError(APIError):
    """404 — requested resource does not exist."""


class RateLimitError(APIError):
    """429 — rate limit exceeded. Check .retry_after for the suggested delay (seconds)."""

    def __init__(
        self,
        status_code: int,
        body: str,
        *,
        request_id: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        message: str | None = None,
        retry_after: str | None = None,
    ) -> None:
        super().__init__(
            status_code,
            body,
            request_id=request_id,
            error_code=error_code,
            error_message=error_message,
            message=message,
        )
        self.retry_after = retry_after


class InvalidRequestError(APIError):
    """4xx (non-401/403/404/429) — malformed or invalid request."""


class APIServerError(APIError):
    """5xx — server-side error."""


class APIConnectionError(SolvaPayError):
    """Network-level error — connection refused, reset, or DNS failure."""


class APITimeoutError(SolvaPayError):
    """Request timed out before the server responded."""


# Back-compat alias: existing `except SolvaPayAPIError` catches and `.status_code` access
# continue to work. Will emit DeprecationWarning in v1.0 pre-tag.
SolvaPayAPIError = APIError
