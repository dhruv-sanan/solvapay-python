"""Tests for _config.py covering all branches."""

from __future__ import annotations

import pytest

from solvapay._config import DEFAULT_BASE_URL, resolve_api_key, resolve_base_url
from solvapay.exceptions import SolvaPayError


def test_resolve_api_key_explicit() -> None:
    assert resolve_api_key("sk_test_explicit") == "sk_test_explicit"


def test_resolve_api_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOLVAPAY_SECRET_KEY", "sk_test_from_env")
    assert resolve_api_key(None) == "sk_test_from_env"


def test_resolve_api_key_missing_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SOLVAPAY_SECRET_KEY", raising=False)
    with pytest.raises(SolvaPayError, match="API key not provided"):
        resolve_api_key(None)


def test_resolve_base_url_explicit() -> None:
    assert resolve_base_url("https://custom.example.com") == "https://custom.example.com"


def test_resolve_base_url_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOLVAPAY_API_BASE_URL", "https://env.example.com")
    assert resolve_base_url(None) == "https://env.example.com"


def test_resolve_base_url_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SOLVAPAY_API_BASE_URL", raising=False)
    assert resolve_base_url(None) == DEFAULT_BASE_URL
