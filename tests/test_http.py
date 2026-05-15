"""Tests for HttpClient.send() and _RequestSpec."""

from __future__ import annotations

import httpx
import respx

from solvapay._http import HttpClient, _RequestSpec


@respx.mock
def test_http_client_send_spec() -> None:
    route = respx.post("https://api.solvapay.test/v1/sdk/test").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    hc = HttpClient(api_key="sk_test_dummy", base_url="https://api.solvapay.test")
    spec = _RequestSpec("POST", "/v1/sdk/test", json={"hello": "world"})
    result = hc.send(spec)
    assert route.called
    assert result == {"ok": True}
    hc.close()
