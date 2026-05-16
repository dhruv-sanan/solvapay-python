"""Exception hierarchy for SolvaPay SDK."""

from __future__ import annotations


class SolvaPayError(Exception):
    """Base exception for all SolvaPay SDK errors."""


class SolvaPayAPIError(SolvaPayError):
    """Raised when the SolvaPay API returns a non-2xx response."""

    def __init__(self, status_code: int, body: str, message: str | None = None) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(message or f"SolvaPay API error {status_code}: {body}")
