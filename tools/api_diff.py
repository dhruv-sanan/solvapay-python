"""CI gate: diff MANIFEST against api_baseline.json.

Fails if any @stable symbol was removed without being @deprecated first.
New @stable additions: always allowed.
@deprecated symbols: allowed regardless.

Usage: uv run python tools/api_diff.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    import solvapay
    from solvapay._stability import MANIFEST

    baseline_path = Path(__file__).parent / "api_baseline.json"
    if not baseline_path.exists():
        print("[api_diff] No baseline found — writing initial baseline.")
        _write_baseline(MANIFEST, baseline_path)
        return 0

    with open(baseline_path) as f:
        baseline: dict[str, dict[str, str | None]] = json.load(f)

    current_stable = {
        name for (_id, name), rec in MANIFEST.items() if rec.tier == "stable"
    }
    baseline_stable = {
        name for name, rec in baseline.items() if rec.get("tier") == "stable"
    }

    removed = baseline_stable - current_stable
    if removed:
        print(f"[api_diff] FAIL — stable symbols removed without @deprecated: {sorted(removed)}")
        return 1

    added = current_stable - baseline_stable
    if added:
        print(f"[api_diff] INFO — new stable symbols (allowed): {sorted(added)}")

    print(f"[api_diff] PASS — {len(current_stable)} stable symbols, {len(added)} new.")
    return 0


def _write_baseline(manifest: dict, path: Path) -> None:
    data = {
        name: {"tier": rec.tier, "removed_in": rec.removed_in}
        for (_id, name), rec in manifest.items()
    }
    path.write_text(json.dumps(data, indent=2, sort_keys=True))
    print(f"[api_diff] Wrote baseline to {path}")


if __name__ == "__main__":
    sys.exit(main())
