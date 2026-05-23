#!/usr/bin/env python
"""Lint invariants checker — mechanically enforces top-10 gotchas (HLD review v2 G5).

Each check corresponds to a numbered entry in python_sdk_plan.md §4.
Exits non-zero if any violation is found; prints file:line for each one.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC = ROOT / "src" / "solvapay"
TESTS = ROOT / "tests"

violations: list[str] = []


def err(path: Path, line: int, msg: str) -> None:
    violations.append(f"{path}:{line}: {msg}")


def source_files(directory: Path) -> list[Path]:
    return sorted(directory.rglob("*.py"))


# ── Check 1: from __future__ import annotations in every src file ──

def check_future_annotations(src_dir: Path) -> None:
    for path in source_files(src_dir):
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:
            continue
        found = False
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module == "__future__"
                and any(a.name == "annotations" for a in node.names)
            ):
                found = True
                break
        if not found:
            err(path, 1, "GOTCHA-10: missing 'from __future__ import annotations'")


# ── Check 2: hmac.compare_digest used for secret comparisons (no == on hmac values) ──

def check_no_hmac_eq(src_dir: Path) -> None:
    for path in source_files(src_dir):
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                # Flag: hmac.hexdigest() == something  or  expected == received
                # Heuristic: variable named 'expected', 'received', 'signature', 'hmac'
                # compared with == rather than hmac.compare_digest
                for child in ast.walk(node):
                    if isinstance(child, ast.Name) and child.id in (
                        "expected",
                        "received",
                        "signature",
                    ):
                        if isinstance(node.ops[0], ast.Eq):
                            err(
                                path,
                                node.lineno,
                                "GOTCHA-SEC: use hmac.compare_digest, not == for HMAC comparison",
                            )
                        break


# ── Check 3: no logging.basicConfig inside src/solvapay/ ──

def check_no_basicconfig(src_dir: Path) -> None:
    for path in source_files(src_dir):
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "basicConfig"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "logging"
            ):
                err(path, node.lineno, "GOTCHA-13: logging.basicConfig must not be called in src/")


# ── Check 4: no asyncio.run() inside src/solvapay/ ──

def check_no_asyncio_run(src_dir: Path) -> None:
    for path in source_files(src_dir):
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "run"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "asyncio"
            ):
                err(path, node.lineno, "HLD-INVARIANT: asyncio.run() must not be called in src/")


# ── Check 5: no nest_asyncio import ──

def check_no_nest_asyncio(src_dir: Path) -> None:
    for path in source_files(src_dir):
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names]
                module = getattr(node, "module", None) or ""
                if "nest_asyncio" in names or "nest_asyncio" in module:
                    err(path, node.lineno, "HLD-INVARIANT: nest_asyncio must not be imported")


# ── Check 6: Idempotency-Key casing consistent ──

def check_idempotency_key_casing(src_dir: Path) -> None:
    correct = "Idempotency-Key"
    for path in source_files(src_dir):
        text = path.read_text()
        for i, line in enumerate(text.splitlines(), 1):
            # Find any quoted string containing "idempotency" (case-insensitive)
            # that is NOT the correct casing
            lower = line.lower()
            if "idempotency-key" in lower:
                idx = lower.index("idempotency-key")
                actual = line[idx : idx + len(correct)]
                if actual != correct:
                    err(path, i, f"GOTCHA-11: Idempotency-Key casing wrong: got {actual!r}")


# ── Check 7: @respx.mock is decorator form in async tests (not context manager) ──

def check_respx_mock_form(test_dir: Path) -> None:
    for path in source_files(test_dir):
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.AsyncWith, ast.With)):
                for item in node.items:
                    call = item.context_expr
                    if (
                        isinstance(call, ast.Call)
                        and isinstance(call.func, ast.Attribute)
                        and call.func.attr == "mock"
                        and isinstance(call.func.value, ast.Name)
                        and call.func.value.id == "respx"
                    ):
                        err(
                            path,
                            node.lineno,
                            "GOTCHA-1: use @respx.mock decorator, not 'with respx.mock()' context manager in tests",
                        )


# ── Check 8: Layer DAG — delegated to lint-imports (informational) ──

def check_layer_dag_note() -> None:
    cfg = ROOT / "tools" / "importlinter.cfg"
    if cfg.exists():
        print(f"SKIP layer-DAG check: enforced by lint-imports ({cfg})")
    else:
        violations.append(f"tools/importlinter.cfg: MISSING — layer DAG not enforced")


# ── Main ──

def main() -> int:
    check_future_annotations(SRC)
    check_no_hmac_eq(SRC)
    check_no_basicconfig(SRC)
    check_no_asyncio_run(SRC)
    check_no_nest_asyncio(SRC)
    check_idempotency_key_casing(SRC)
    check_respx_mock_form(TESTS)
    check_layer_dag_note()

    if violations:
        print(f"\nInvariant violations ({len(violations)}):")
        for v in violations:
            print(f"  {v}")
        return 1

    print(f"All invariants OK ({len(source_files(SRC))} source files checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
