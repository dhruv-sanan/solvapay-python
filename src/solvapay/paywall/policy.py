"""PolicyEnforcer Protocol stub — real impls land in experimental (HLD V1.6)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class PolicyEnforcer(Protocol):
    """Pluggable policy for spending limits and agent identity."""

    def check(self, customer_ref: str, product: str, **context: Any) -> bool:
        """Return True if the operation is permitted."""
        ...
