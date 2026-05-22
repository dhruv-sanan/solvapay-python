"""Runtime 2: LangChain agent — same web_search tool via monetize_tool.

Run: uv run python agent_langchain.py
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

from solvapay import SolvaPay
from solvapay.adapters.langchain import monetize_tool
from tool import web_search, PRODUCT_REF

sv = SolvaPay()

try:
    from langchain_core.tools import Tool
except ImportError as exc:
    raise SystemExit(
        "LangChain not installed. Run: pip install 'solvapay-python[langchain]'"
    ) from exc


def _run(*, customer_ref: str = "", query: str = "", **kw: object) -> object:
    return web_search(customer_ref=customer_ref, query=query)


lc_tool = Tool.from_function(
    name="web_search",
    func=_run,
    description="Search the web. Requires customer_ref kwarg.",
)

paid_tool = monetize_tool(lc_tool, product=PRODUCT_REF, client=sv)

if __name__ == "__main__":
    customer = os.getenv("DEMO_CUSTOMER_REF", "cus_demo")
    result = paid_tool.func(customer_ref=customer, query="SolvaPay Python SDK")
    print(result)
