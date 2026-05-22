"""Runtime 3: Raw AsyncSolvaPay — programmatic gate check + direct tool call.

Run: uv run python script_async.py
"""

from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

from solvapay import AsyncSolvaPay
from tool import web_search, PRODUCT_REF


async def main() -> None:
    customer = os.getenv("DEMO_CUSTOMER_REF", "cus_demo")

    async with AsyncSolvaPay() as sv:
        limits = await sv.limits.acheck(
            customer_ref=customer,
            product_ref=PRODUCT_REF,
        )
        if not limits.within_limits:
            print(f"Blocked. remaining={limits.remaining}")
            decision = await sv.checkout.acreate_session(
                customer_ref=customer, product_ref=PRODUCT_REF
            )
            print(f"Checkout URL: {decision.checkout_url}")
            return

        # Gate passed — call the tool directly (no paywall overhead)
        results = web_search.__wrapped__(  # type: ignore[attr-defined]
            customer_ref=customer, query="async SolvaPay demo"
        )
        print("Results:", results)


if __name__ == "__main__":
    asyncio.run(main())
