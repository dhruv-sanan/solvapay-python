"""SolvaPay paywall package.

Public API (stable):
    PaywallRequired — exception raised when limits are exceeded
    require         — sync decorator
    require_async   — async decorator

New in v0.8:
    Paywall         — sync gate class (HLD V1.6)
    AsyncPaywall    — async gate class (HLD V1.6)
    payable_tool    — stamps __solvapay_meta__ (HLD V1.17)
"""

from __future__ import annotations

from solvapay.paywall.core import AsyncPaywall, Paywall, PaywallRequired
from solvapay.paywall.decorators import payable_tool, require, require_async
from solvapay.paywall.meta import PayableToolMeta
from solvapay.paywall.resolvers import KwargsResolver, PositionalResolver, PydanticBodyResolver

__all__ = [
    "AsyncPaywall",
    "KwargsResolver",
    "PayableToolMeta",
    "Paywall",
    "PaywallRequired",
    "PositionalResolver",
    "PydanticBodyResolver",
    "payable_tool",
    "require",
    "require_async",
]
