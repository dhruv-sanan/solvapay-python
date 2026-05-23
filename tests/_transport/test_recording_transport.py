"""Tests for RecordingTransport — cassette record and replay."""

from __future__ import annotations

import json

from solvapay._transport import Headers, RequestSpec, ResponseMetadata, ResponseSpec
from solvapay._transport.middleware import RecordingTransport


def _ok_response(body: dict | None = None) -> ResponseSpec:
    return ResponseSpec(
        body=body if body is not None else {"result": "ok"},
        metadata=ResponseMetadata(200, Headers({}), 0),
    )


class _MockInner:
    def __init__(self, response: ResponseSpec) -> None:
        self.calls = 0
        self._resp = response

    def send(self, spec: RequestSpec) -> ResponseSpec:
        self.calls += 1
        return self._resp

    def close(self) -> None:
        pass


def _spec() -> RequestSpec:
    return RequestSpec(method="GET", url="/v1/test", headers=Headers({}), json=None)


def test_records_to_cassette_on_first_call(tmp_path) -> None:
    cassette = str(tmp_path / "test.json")
    inner = _MockInner(_ok_response({"result": "recorded"}))
    transport = RecordingTransport(inner, cassette_path=cassette)

    resp = transport.send(_spec())
    assert resp.body == {"result": "recorded"}
    assert inner.calls == 1

    with open(cassette) as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["response"]["status_code"] == 200
    assert data[0]["response"]["body"] == {"result": "recorded"}


def test_replays_from_cassette_without_hitting_inner(tmp_path) -> None:
    cassette = str(tmp_path / "replay.json")
    # Pre-write a cassette
    cassette_data = [
        {
            "request": {"method": "GET", "url": "/v1/test", "json": None},
            "response": {"status_code": 200, "body": {"replayed": True}, "headers": {}},
        }
    ]
    with open(cassette, "w") as f:
        json.dump(cassette_data, f)

    inner = _MockInner(_ok_response())
    transport = RecordingTransport(inner, cassette_path=cassette)

    resp = transport.send(_spec())
    assert resp.body == {"replayed": True}
    assert inner.calls == 0  # inner never called during replay
