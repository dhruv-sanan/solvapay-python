"""FastMCP server demo — two tools gated by SolvaPay paywall.

Run:
    uv sync
    cp .env.example .env  # then fill in
    uv run python server.py     # stdio mode for Claude Desktop / mcp-inspector

Test from terminal:
    npx @modelcontextprotocol/inspector uv run python server.py
"""
from __future__ import annotations

import functools
import os
from typing import Any

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP

from solvapay import SolvaPay, paywall
from solvapay.paywall import PaywallRequired

load_dotenv()

PRODUCT_REF = os.environ["SOLVAPAY_PRODUCT_REF"]
DEMO_CUSTOMER_REF = os.environ.get("SOLVAPAY_DEMO_CUSTOMER_REF", "cus_demo")

# Single shared SolvaPay client — reads SOLVAPAY_SECRET_KEY from env
sv = SolvaPay()

mcp = FastMCP("solvapay-paywall-demo")


def _gated(fn: Any) -> Any:
    """Wrap fn in @paywall.require and convert PaywallRequired into a structured
    response the LLM can show the user instead of a stack trace.
    """
    protected = paywall.require(product=PRODUCT_REF, client=sv)(fn)

    @functools.wraps(fn)  # preserves __wrapped__ so FastMCP reads the real signature
    def wrapper(**kwargs: Any) -> Any:
        try:
            return protected(**kwargs)
        except PaywallRequired as exc:
            return {
                "paywall_required": True,
                "checkout_url": exc.checkout_url,
                "message": "This tool is paywalled. Pay at the URL to unlock.",
            }

    return wrapper


@mcp.tool()
@_gated
def summarize_url(*, url: str, customer_ref: str = DEMO_CUSTOMER_REF) -> dict[str, Any]:
    """Fetch a URL and return a 1-paragraph summary.

    Gated at $0.02/call by SolvaPay. customer_ref defaults to the demo
    customer for quick testing — override per-call in production.

    Args:
        url: HTTP(S) URL to fetch and summarize.
        customer_ref: SolvaPay customer reference. Defaults to demo customer.

    Returns:
        {"url": ..., "preview": ..., "char_count": ...}
        OR {"paywall_required": True, "checkout_url": ...} if limit exceeded.
    """
    response = httpx.get(url, follow_redirects=True, timeout=10)
    response.raise_for_status()
    text = response.text
    return {
        "url": url,
        "preview": text[:280] + ("…" if len(text) > 280 else ""),
        "char_count": len(text),
    }


@mcp.tool()
@_gated
def analyze_text(*, text: str, customer_ref: str = DEMO_CUSTOMER_REF) -> dict[str, Any]:
    """Word/char/sentence breakdown of input text.

    Gated at $0.05/call by SolvaPay.

    Args:
        text: Text to analyze.
        customer_ref: SolvaPay customer reference. Defaults to demo customer.

    Returns:
        {"word_count": int, "char_count": int, "sentence_count": int, "avg_word_len": float}
        OR {"paywall_required": True, "checkout_url": ...} if limit exceeded.
    """
    words = text.split()
    sentences = text.count(".") + text.count("!") + text.count("?")
    return {
        "word_count": len(words),
        "char_count": len(text),
        "sentence_count": sentences,
        "avg_word_len": round(sum(len(w) for w in words) / max(len(words), 1), 2),
    }


if __name__ == "__main__":
    mcp.run()
