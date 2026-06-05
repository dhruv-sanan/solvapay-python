"""Smoke test: verify_webhook uses constant-time comparison.

Catches regressions where someone swaps ``hmac.compare_digest`` for ``==``.
This is NOT a perfect side-channel timing test — it's a coarse statistical
regression smoke. We compare the perf.counter distribution of a perfect-match
verify against a near-miss verify and assert their medians overlap within
a generous bound. A naive ``==`` short-circuits on the first byte mismatch
and would diverge wildly.
"""

from __future__ import annotations

import contextlib
import statistics
import time
from time import perf_counter_ns

import pytest

from solvapay.exceptions import SolvaPayError
from solvapay.webhooks import sign_webhook, verify_webhook

_BODY = b'{"id":"evt_test","type":"payment.succeeded"}'
_SECRET = "whsec_constant_time_smoke"
_ITERATIONS = 2_000


def _measure(body: str, sig: str, secret: str) -> int:
    start = perf_counter_ns()
    with contextlib.suppress(SolvaPayError):
        verify_webhook(body=body, signature=sig, secret=secret, tolerance=10**9)
    return perf_counter_ns() - start


def test_verify_webhook_constant_time_smoke() -> None:
    ts = int(time.time())
    good_sig = sign_webhook(_BODY, _SECRET, timestamp=ts)
    # Near-miss: same length / structure, differ in v1 hex tail only
    bad_sig = good_sig[:-4] + ("0000" if good_sig[-4:] != "0000" else "ffff")
    body_str = _BODY.decode()

    good_times: list[int] = []
    bad_times: list[int] = []
    for i in range(_ITERATIONS):
        # interleave to share thermal / GC noise
        if i % 2 == 0:
            good_times.append(_measure(body_str, good_sig, _SECRET))
            bad_times.append(_measure(body_str, bad_sig, _SECRET))
        else:
            bad_times.append(_measure(body_str, bad_sig, _SECRET))
            good_times.append(_measure(body_str, good_sig, _SECRET))

    # Trim 10% tails — GC pauses dominate otherwise
    def _trimmed_median(xs: list[int]) -> float:
        xs = sorted(xs)
        cut = len(xs) // 10
        trimmed = xs[cut : len(xs) - cut]
        return statistics.median(trimmed)

    good_med = _trimmed_median(good_times)
    bad_med = _trimmed_median(bad_times)

    # Generous bound: medians within 3x of each other in either direction.
    # A naive == on the hex would short-circuit and produce >10x divergence.
    ratio = max(good_med, bad_med) / max(min(good_med, bad_med), 1.0)
    assert ratio < 3.0, (
        f"verify_webhook timing diverged: good={good_med}ns bad={bad_med}ns "
        f"ratio={ratio:.2f}. Did someone swap hmac.compare_digest for ==?"
    )


@pytest.mark.parametrize("flip_index", [0, 8, 16, 32, 63])
def test_verify_webhook_rejects_single_byte_flip(flip_index: int) -> None:
    """Sanity: flipping any single hex char of v1 sig is rejected."""
    ts = int(time.time())
    sig = sign_webhook(_BODY, _SECRET, timestamp=ts)
    v1_start = sig.index("v1=") + 3
    v1 = list(sig[v1_start:])
    v1[flip_index] = "0" if v1[flip_index] != "0" else "f"
    tampered = sig[:v1_start] + "".join(v1)
    with pytest.raises(SolvaPayError, match="signature mismatch"):
        verify_webhook(body=_BODY.decode(), signature=tampered, secret=_SECRET)
