"""Tests for structured error hierarchy and request_id surfacing."""

from __future__ import annotations

import httpx
import pytest
import respx

from solvapay import SolvaPay
from solvapay.exceptions import (
    APIConnectionError,
    APIError,
    APIServerError,
    APITimeoutError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    SolvaPayAPIError,
)

BASE = "https://api.solvapay.test"


@respx.mock
def test_401_raises_authentication_error_with_request_id(client: SolvaPay) -> None:
    respx.get(f"{BASE}/v1/sdk/customers/cus_x").mock(
        return_value=httpx.Response(
            401,
            json={"error": {"code": "unauthorized", "message": "Bad key"}},
            headers={"x-request-id": "req_abc123"},
        )
    )
    with pytest.raises(AuthenticationError) as exc_info:
        client.get_customer("cus_x")
    err = exc_info.value
    assert err.status_code == 401
    assert err.request_id == "req_abc123"
    assert err.error_code == "unauthorized"


@respx.mock
def test_429_raises_rate_limit_error_with_retry_after(client: SolvaPay) -> None:
    respx.get(f"{BASE}/v1/sdk/customers/cus_x").mock(
        return_value=httpx.Response(
            429,
            json={"error": {"message": "Too many requests"}},
            headers={"Retry-After": "30"},
        )
    )
    with pytest.raises(RateLimitError) as exc_info:
        client.get_customer("cus_x")
    assert exc_info.value.status_code == 429
    assert exc_info.value.retry_after == "30"


@respx.mock
def test_500_raises_api_server_error(client: SolvaPay) -> None:
    respx.get(f"{BASE}/v1/sdk/customers/cus_x").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )
    with pytest.raises(APIServerError) as exc_info:
        client.get_customer("cus_x")
    assert exc_info.value.status_code == 500


@respx.mock
def test_404_raises_not_found_error(client: SolvaPay) -> None:
    respx.get(f"{BASE}/v1/sdk/customers/cus_missing").mock(
        return_value=httpx.Response(404, json={"error": {"message": "Not found"}})
    )
    with pytest.raises(NotFoundError) as exc_info:
        client.get_customer("cus_missing")
    assert exc_info.value.status_code == 404


@respx.mock
def test_connection_refused_raises_api_connection_error(client: SolvaPay) -> None:
    respx.get(f"{BASE}/v1/sdk/customers/cus_x").mock(
        side_effect=httpx.ConnectError("Connection refused")
    )
    with pytest.raises(APIConnectionError):
        client.get_customer("cus_x")


@respx.mock
def test_timeout_raises_api_timeout_error(client: SolvaPay) -> None:
    respx.get(f"{BASE}/v1/sdk/customers/cus_x").mock(side_effect=httpx.TimeoutException("Timeout"))
    with pytest.raises(APITimeoutError):
        client.get_customer("cus_x")


@respx.mock
def test_all_api_errors_carry_request_id_from_header(client: SolvaPay) -> None:
    respx.get(f"{BASE}/v1/sdk/customers/cus_x").mock(
        return_value=httpx.Response(
            403,
            text="Forbidden",
            headers={"x-request-id": "req_xyz789"},
        )
    )
    with pytest.raises(APIError) as exc_info:
        client.get_customer("cus_x")
    assert exc_info.value.request_id == "req_xyz789"


@respx.mock
def test_legacy_solvapay_api_error_alias_still_catches(client: SolvaPay) -> None:
    respx.get(f"{BASE}/v1/sdk/customers/cus_x").mock(
        return_value=httpx.Response(401, text="Unauthorized")
    )
    with pytest.raises(SolvaPayAPIError):
        client.get_customer("cus_x")
    assert SolvaPayAPIError is APIError
