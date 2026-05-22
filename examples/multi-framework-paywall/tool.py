"""The payable tool — shared by all three runtimes.

@payable_tool stamps __solvapay_meta__ so FastMCP, LangChain,
and the raw async script all use the same paywall gate.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

from solvapay import SolvaPay
from solvapay.adapters.mcp import payable_tool

_sv = SolvaPay()

PRODUCT_REF = os.getenv("SOLVAPAY_PRODUCT_REF", "prd_search")


@payable_tool(product=PRODUCT_REF, client=_sv)
def web_search(*, customer_ref: str, query: str, max_results: int = 5) -> list[str]:
    """Search the web and return top results.

    Args:
        customer_ref: SolvaPay customer reference.
        query: Search query string.
        max_results: Maximum number of results to return.

    Returns:
        List of result strings.
    """
    # Stub: replace with real search integration
    return [f"Result {i} for '{query}'" for i in range(1, max_results + 1)]
