"""Microbenchmark harness.

Run with:
    uv run pytest tests/benchmarks/ --benchmark-only
    # requires: pip install solvapay-python[bench]  OR  uv add pytest-benchmark

NOT included in the default pytest run (excluded via addopts in pyproject.toml).
No merge gate; v1.0 graduates these to gating once cold-import and construction
budgets are locked (HLD §V1.20).
"""

from __future__ import annotations

import time as _time
from typing import Any

import pytest

pytestmark = pytest.mark.benchmark


def test_client_construction(benchmark: Any) -> None:
    """SolvaPay() construction time. Target: <1 ms at v1.0 (HLD §V1.20)."""
    from solvapay import SolvaPay

    benchmark(SolvaPay, api_key="sk_test_bench")


def test_verify_webhook_per_call(benchmark: Any) -> None:
    """verify_webhook per-call cost (HMAC-SHA256 + header parse)."""
    from solvapay.webhooks import sign_webhook, verify_webhook

    secret = "whsec_test_bench"
    body = b'{"id":"evt_bench","type":"payment.succeeded"}'
    ts = int(_time.time())
    sig = sign_webhook(body, secret, timestamp=ts)

    # verify_webhook is fully keyword-only; wrap in lambda for benchmark.
    benchmark(lambda: verify_webhook(body=body.decode(), signature=sig, secret=secret))


def test_from_payload_derivation(benchmark: Any) -> None:
    """idempotency.from_payload() derivation cost (SHA-256)."""
    from solvapay.idempotency import from_payload

    benchmark(from_payload, "ensure_customer", "cus_bench", "ext_ref_abc")
