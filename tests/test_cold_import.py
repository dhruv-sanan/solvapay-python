"""Cold-import baseline harness.

Measures ``python -X importtime -c "import solvapay"`` and compares against
a committed per-platform baseline.

Behaviour:
- **CI** (``CI=true`` env var set by GitHub Actions): always prints the
  measurement; never fails. GitHub runners have no persistent baseline across
  fresh checkouts, so asserting would produce false failures on every run.
- **Local**: writes a per-platform baseline on first run; subsequent runs assert
  within 1.5x. Catches cold-import regressions introduced during development.

Platform keys: ``sys.platform`` (``darwin``, ``linux``, ``win32``).
The hard <200 ms CI gate is a v1.0 feature (HLD §V1.20); v0.9.2 measures only.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

BASELINE_PATH = Path(__file__).parent / "_baselines" / "cold_import.json"
BASELINE_PATH.parent.mkdir(exist_ok=True)
REGRESSION_FACTOR = 1.5
PLATFORM = sys.platform  # e.g. "darwin", "linux", "win32"
IN_CI = os.environ.get("CI", "").lower() in ("true", "1")


def _measure_import_ms() -> float:
    result = subprocess.run(
        [sys.executable, "-X", "importtime", "-c", "import solvapay"],
        capture_output=True,
        text=True,
    )
    # importtime writes to stderr.
    # Each line: "import time:  <self_us> | <cumulative_us> | <module>"
    lines = [ln for ln in result.stderr.splitlines() if "import time:" in ln]
    if not lines:
        raise RuntimeError(f"No importtime output captured.\nstderr:\n{result.stderr}")
    # The outermost module (solvapay) has the highest cumulative value.
    cumulative_us = max(
        int(m.group(1)) for ln in lines if (m := re.search(r"import time:\s+\d+\s+\|\s+(\d+)", ln))
    )
    return cumulative_us / 1000.0  # µs → ms


def test_cold_import_baseline() -> None:
    """Measure cold-import time. Assert vs baseline locally; print-only in CI."""
    current_ms = _measure_import_ms()

    if IN_CI:
        # CI has no persistent state; just report the number.
        print(f"\n[cold-import] CI platform={PLATFORM} current={current_ms:.1f} ms (no assertion)")
        assert current_ms < 2000, (
            f"Cold-import took {current_ms:.0f} ms — suspiciously slow even for CI"
        )
        return

    # Local: per-platform baseline regression gate.
    baselines: dict[str, float] = {}
    if BASELINE_PATH.exists():
        raw = json.loads(BASELINE_PATH.read_text())
        # Support legacy flat format {"cold_import_ms": X}.
        if "cold_import_ms" in raw and not any(k in raw for k in ("darwin", "linux", "win32")):
            baselines = {PLATFORM: raw["cold_import_ms"]}
        else:
            baselines = raw

    if PLATFORM not in baselines:
        assert current_ms < 2000, (
            f"Cold-import took {current_ms:.0f} ms on first run — suspiciously slow"
        )
        baselines[PLATFORM] = round(current_ms, 2)
        BASELINE_PATH.write_text(json.dumps(baselines, sort_keys=True))
        print(f"\n[cold-import] {PLATFORM} baseline written: {current_ms:.1f} ms")
        return

    baseline_ms: float = baselines[PLATFORM]
    limit_ms = baseline_ms * REGRESSION_FACTOR

    print(
        f"\n[cold-import] platform={PLATFORM} current={current_ms:.1f} ms  "
        f"baseline={baseline_ms:.1f} ms  limit={limit_ms:.1f} ms"
    )
    assert current_ms <= limit_ms, (
        f"Cold-import regression on {PLATFORM}: {current_ms:.1f} ms > {limit_ms:.1f} ms "
        f"(baseline={baseline_ms:.1f} ms x {REGRESSION_FACTOR})"
    )
