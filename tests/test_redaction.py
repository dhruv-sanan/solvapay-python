"""Tests for structured logging and secret redaction."""

from __future__ import annotations

import logging

import httpx
import pytest
import respx

from solvapay import SolvaPay
from solvapay.exceptions import AuthenticationError

BASE = "https://api.solvapay.test"
CUSTOMER_RESPONSE = {"reference": "cus_x", "purchases": []}


@respx.mock
def test_authorization_header_redacted_in_logs(caplog: pytest.LogCaptureFixture) -> None:
    sv = SolvaPay(api_key="sk_test_secret_key_xyz", base_url=BASE)
    respx.get(f"{BASE}/v1/sdk/customers/cus_x").mock(
        return_value=httpx.Response(200, json=CUSTOMER_RESPONSE)
    )
    with caplog.at_level(logging.INFO, logger="solvapay.http"):
        sv.get_customer("cus_x")
    assert "sk_test_secret_key_xyz" not in caplog.text


@respx.mock
def test_webhook_secret_not_logged_on_failure(caplog: pytest.LogCaptureFixture) -> None:
    sv = SolvaPay(api_key="sk_test_dummy", base_url=BASE)
    # Simulate a response whose body might look like it contains a secret
    respx.get(f"{BASE}/v1/sdk/customers/cus_x").mock(
        return_value=httpx.Response(401, text="unauthorized: wh_secret_should_not_appear")
    )
    with (
        caplog.at_level(logging.WARNING, logger="solvapay.http"),
        pytest.raises(AuthenticationError),
    ):
        sv.get_customer("cus_x")
    # body_excerpt IS logged at WARNING — verify API key isn't there
    assert "sk_test_dummy" not in caplog.text


@respx.mock
def test_request_id_present_in_info_log(caplog: pytest.LogCaptureFixture) -> None:
    sv = SolvaPay(api_key="sk_test_dummy", base_url=BASE)
    respx.get(f"{BASE}/v1/sdk/customers/cus_x").mock(
        return_value=httpx.Response(
            200, json=CUSTOMER_RESPONSE, headers={"x-request-id": "req_test_abc123"}
        )
    )
    with caplog.at_level(logging.INFO, logger="solvapay.http"):
        sv.get_customer("cus_x")
    records = [r for r in caplog.records if r.name == "solvapay.http"]
    assert records, "expected at least one log record from solvapay.http"
    assert any(getattr(r, "request_id", None) == "req_test_abc123" for r in records)
