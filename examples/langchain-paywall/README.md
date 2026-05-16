# LangChain paywall example

Shows how to gate a LangChain tool behind a [SolvaPay](https://solvapay.com) paywall using `monetize_tool`.

## What it does

1. Wraps a custom `web_search` tool with `monetize_tool`
2. Runs a LangChain agent that calls the tool
3. When the customer is within limits → tool runs normally
4. When the customer is over-limit → agent receives a structured dict with `checkout_url` and surfaces it to the user

## Setup

```bash
cp .env.example .env
# Fill in SOLVAPAY_SECRET_KEY, OPENAI_API_KEY, SOLVAPAY_PRODUCT_REF
```

## Run

```bash
uv run python agent.py
```

## Key code

```python
from solvapay.langchain import monetize_tool

raw_tool = Tool.from_function(name="web_search", func=do_search, description="...")
paid_tool = monetize_tool(raw_tool, product="prd_your_product")
```

The wrapped tool returns a plain dict when gated:

```python
{
    "paywall_required": True,
    "state": "upgrade_required",
    "message": "You don't have an active plan for this tool. Call the `upgrade` tool to pick a plan.",
    "checkout_url": "https://solvapay.com/c/...",
    "recovery_tool": "upgrade",
}
```

LangChain agents see this as the tool result and can relay the `checkout_url` to the user.
