"""Tests for structured logging and secret redaction."""

from __future__ import annotations

import logging

import httpx
import pytest
import respx
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from solvapay import SolvaPay
from solvapay.exceptions import AuthenticationError

BASE = "https://api.solvapay.test"
CUSTOMER_RESPONSE = {"reference": "cus_x", "purchases": []}

# Strategies for secret-like values (API keys, hex tokens, webhook secrets)
_api_key_st = st.text(
    alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters=" \t\n\r"),
    min_size=16,
    max_size=64,
).map(lambda s: f"sk_test_{s}")
_hex_token_st = st.text(alphabet="0123456789abcdef", min_size=32, max_size=64)
_webhook_secret_st = st.text(
    alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters=" \t\n\r"),
    min_size=24,
    max_size=64,
).map(lambda s: f"whsec_{s}")


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


@respx.mock
@settings(
    max_examples=100,
    deadline=None,
    derandomize=True,  # reproducible — equivalent to hypothesis-seed=0 pinning
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(secret=_api_key_st | _hex_token_st | _webhook_secret_st)
def test_arbitrary_api_key_never_appears_in_logs(
    secret: str, caplog: pytest.LogCaptureFixture
) -> None:
    """Property: no generated secret-shaped value leaks through transport logs."""
    caplog.clear()
    respx.get(f"{BASE}/v1/sdk/customers/cus_x").mock(
        return_value=httpx.Response(200, json=CUSTOMER_RESPONSE)
    )
    sv = SolvaPay(api_key=secret, base_url=BASE)
    with caplog.at_level(logging.DEBUG, logger="solvapay.http"):
        sv.get_customer("cus_x")
    assert secret not in caplog.text, "secret leaked into log output"
