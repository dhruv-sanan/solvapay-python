"""Stability manifest (HLD V1.2).

stable(X) -> X     — returns identity; registers in MANIFEST. isinstance() works.
experimental(X)    — returns identity; emits RuntimeWarning once per process.
deprecated(*)      — returns identity; registers deprecation in MANIFEST.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any, TypeVar

T = TypeVar("T")

_experimental_warned: set[int] = set()


@dataclass
class StabilityRecord:
    tier: str  # "stable" | "experimental" | "deprecated"
    exported_name: str
    removed_in: str | None = None


# Keyed by (id(symbol), exported_name) — allows same object under multiple aliases (HLD SM2)
MANIFEST: dict[tuple[int, str], StabilityRecord] = {}


def stable(symbol: T) -> T:
    """Return symbol unchanged; register as stable in MANIFEST (HLD SM1)."""
    name = getattr(symbol, "__name__", repr(symbol))
    MANIFEST[(id(symbol), name)] = StabilityRecord("stable", name)
    return symbol


def experimental(symbol: T) -> T:
    """Return symbol unchanged; emit RuntimeWarning once per process on first import."""
    name = getattr(symbol, "__name__", repr(symbol))
    symbol_id = id(symbol)
    if symbol_id not in _experimental_warned:
        _experimental_warned.add(symbol_id)
        warnings.warn(
            f"solvapay.{name} is experimental and may change without notice.",
            RuntimeWarning,
            stacklevel=2,
        )
    MANIFEST[(symbol_id, name)] = StabilityRecord("experimental", name)
    return symbol


def deprecated(*, removed_in: str) -> Any:
    """Decorator factory. Return symbol unchanged; register deprecation in MANIFEST."""

    def decorator(symbol: T) -> T:
        name = getattr(symbol, "__name__", repr(symbol))
        MANIFEST[(id(symbol), name)] = StabilityRecord("deprecated", name, removed_in=removed_in)
        return symbol

    return decorator
