# solvapay-python

Community Python SDK for [SolvaPay](https://solvapay.com) — agent-native payment rails.

```bash
pip install solvapay-python
```

## Quickstart

```python
from solvapay import SolvaPay

sv = SolvaPay()  # reads SOLVAPAY_SECRET_KEY env var

# Ensure a customer exists
customer_ref = sv.customers.ensure("user_123")

# Create a checkout session
session = sv.checkout.create_session(
    customer_ref=customer_ref,
    product_ref="prd_0QKI8NHF",
)
print(session.checkout_url)
```

## Async

```python
from solvapay import AsyncSolvaPay

async with AsyncSolvaPay() as sv:
    session = await sv.checkout.acreate_session(
        customer_ref="cus_123",
        product_ref="prd_0QKI8NHF",
    )
```

## MCP (payable tools)

```python
from solvapay.paywall import payable_tool

@payable_tool(product="prd_0QKI8NHF")
def web_search(*, customer_ref: str, query: str) -> list[str]:
    ...
```

## API version pinning

```python
sv = SolvaPay(api_version="2026-05-22")  # pins Solvapay-Version header
sv = SolvaPay(api_version=None)          # omits header
```

## Install extras

```bash
pip install "solvapay-python[mcp]"       # FastMCP adapter
pip install "solvapay-python[langchain]" # LangChain adapter
pip install "solvapay-python[retry]"     # RetryTransport (tenacity)
pip install "solvapay-python[asgi]"      # ASGI webhook adapter
```
