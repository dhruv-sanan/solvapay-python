"""Cold-import baseline harness.

Runs ``python -X importtime -c "import solvapay"`` via subprocess, parses the
highest cumulative time from the importtime output, and writes a baseline on
first run. Subsequent runs assert the current time is within 1.5x the baseline.

CI prints the absolute ms value so regressions are visible in the test name.
The hard <200 ms gate is a v1.0 feature (HLD §V1.20); this only measures.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

BASELINE_PATH = Path(__file__).parent / "_baselines" / "cold_import.json"
BASELINE_PATH.parent.mkdir(exist_ok=True)
REGRESSION_FACTOR = 1.5


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
    """Measure cold-import time and assert within 1.5x of committed baseline."""
    current_ms = _measure_import_ms()

    if not BASELINE_PATH.exists():
        # Sanity: import must complete in <2 s even on first run (no regression).
        assert current_ms < 2000, (
            f"Cold-import took {current_ms:.0f} ms on first run — suspiciously slow"
        )
        BASELINE_PATH.write_text(json.dumps({"cold_import_ms": round(current_ms, 2)}))
        print(f"\n[cold-import] Baseline written: {current_ms:.1f} ms")
        return

    baseline = json.loads(BASELINE_PATH.read_text())
    baseline_ms: float = baseline["cold_import_ms"]
    limit_ms = baseline_ms * REGRESSION_FACTOR

    print(
        f"\n[cold-import] current={current_ms:.1f} ms  "
        f"baseline={baseline_ms:.1f} ms  limit={limit_ms:.1f} ms"
    )
    assert current_ms <= limit_ms, (
        f"Cold-import regression: {current_ms:.1f} ms > {limit_ms:.1f} ms "
        f"(baseline={baseline_ms:.1f} ms x {REGRESSION_FACTOR})"
    )
