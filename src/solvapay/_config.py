"""Environment configuration loading."""

from __future__ import annotations

import os

DEFAULT_BASE_URL = "https://api.solvapay.com"


def resolve_api_key(explicit: str | None) -> str:
    key = explicit or os.environ.get("SOLVAPAY_SECRET_KEY")
    if not key:
        from solvapay.exceptions import SolvaPayError

        raise SolvaPayError(
            "SolvaPay API key not provided. Pass api_key=... or set SOLVAPAY_SECRET_KEY env var."
        )
    return key


def resolve_base_url(explicit: str | None) -> str:
    return explicit or os.environ.get("SOLVAPAY_API_BASE_URL") or DEFAULT_BASE_URL
