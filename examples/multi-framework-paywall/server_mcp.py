"""Runtime 1: FastMCP server — exposes web_search as a paywalled MCP tool.

Run: uv run python server_mcp.py
"""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

try:
    import fastmcp
except ImportError as exc:
    raise SystemExit(
        "FastMCP not installed. Run: pip install 'solvapay-python[mcp]'"
    ) from exc

from fastmcp import FastMCP

from solvapay.adapters.mcp import register_payable_tool_fastmcp
from tool import web_search

mcp = FastMCP("SolvaPay Demo — Web Search")
register_payable_tool_fastmcp(mcp, web_search)

if __name__ == "__main__":
    mcp.run()
