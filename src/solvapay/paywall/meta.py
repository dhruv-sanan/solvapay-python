"""PayableToolMeta — frozen descriptor stamped onto payable functions (HLD V1.17 AD1)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PayableToolMeta:
    """Stamped as fn.__solvapay_meta__ by @payable_tool.

    _meta_version is locked at 1 (HLD AD1). Never break this shape.
    """

    _meta_version: int = 1
    product: str = ""
    plan: str | None = None
    customer_ref_resolver: str = "customer_ref"
