"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from solvapay import AsyncSolvaPay, SolvaPay


@pytest.fixture
def client() -> SolvaPay:
    return SolvaPay(api_key="sk_test_dummy", base_url="https://api.solvapay.test")


@pytest.fixture
def async_client() -> AsyncSolvaPay:
    return AsyncSolvaPay(api_key="sk_test_dummy", base_url="https://api.solvapay.test")
