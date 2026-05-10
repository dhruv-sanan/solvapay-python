"""Smoke test for the FastMCP paywall demo.

Spawns server.py via FastMCP's PythonStdioTransport and invokes both tools —
prints the result or the paywall response.

Run: uv run python claim.py
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from fastmcp.client import Client
from fastmcp.client.transports import PythonStdioTransport


SERVER = Path(__file__).parent / "server.py"


async def main() -> None:
    print("Starting FastMCP server in subprocess…")
    transport = PythonStdioTransport(SERVER)

    async with Client(transport) as client:
        tools = await client.list_tools()
        print(f"\nTools available: {[t.name for t in tools]}")

        print("\n— summarize_url —")
        r1 = await client.call_tool("summarize_url", {"url": "https://example.com"})
        print(r1)

        print("\n— analyze_text —")
        r2 = await client.call_tool("analyze_text", {"text": "Hello world. This is a test."})
        print(r2)


if __name__ == "__main__":
    asyncio.run(main())
