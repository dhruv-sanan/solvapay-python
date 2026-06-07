"""Belt-and-suspenders enforcement of the HLD §V1.1 layer DAG.

The primary gate is the CI step that runs ``lint-imports`` directly. This
test shells out to the same command so that ``pytest`` also fails locally
if someone introduces an upward import without re-running ``lint-imports``.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG = REPO_ROOT / "tools" / "importlinter.cfg"


def test_layered_dag_contract_holds() -> None:
    lint_imports = shutil.which("lint-imports")
    if lint_imports is None:
        pytest.skip("lint-imports not on PATH; CI runs it directly")
    result = subprocess.run(
        [lint_imports, "--config", str(CONFIG)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"lint-imports failed (rc={result.returncode}).\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
