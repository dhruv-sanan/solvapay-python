# solvapay-python

Community Python SDK for [SolvaPay](https://solvapay.com) — agentic payment rails.  
`pip install solvapay-python` · Python 3.10+ · [PyPI](https://pypi.org/project/solvapay-python/)

[![CI](https://github.com/dhruv-sanan/solvapay-python/actions/workflows/ci.yml/badge.svg)](https://github.com/dhruv-sanan/solvapay-python/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/solvapay-python.svg)](https://pypi.org/project/solvapay-python/)

---

## AI-agent ecosystems

### MCP (Claude Desktop / Claude Code)

```python
from solvapay.adapters.mcp import payable_tool, register_payable_tool_fastmcp
from fastmcp import FastMCP

mcp = FastMCP("My App")

@payable_tool(product="prd_search")
def web_search(*, customer_ref: str, query: str) -> list[str]:
    """Search the web."""
    return do_real_search(query)

register_payable_tool_fastmcp(mcp, web_search)
mcp.run()
```

`pip install 'solvapay-python[mcp]'`

### LangChain

```python
from solvapay.adapters.langchain import monetize_tool
from langchain_core.tools import Tool

raw = Tool.from_function(name="search", func=do_search, description="Search the web.")
paid = monetize_tool(raw, product="prd_search")
# Returns {"paywall_required": True, "checkout_url": "..."} on block
```

`pip install 'solvapay-python[langchain]'`

### Raw async

```python
from solvapay import AsyncSolvaPay

async with AsyncSolvaPay() as sv:
    limits = await sv.limits.acheck(customer_ref="cus_123", product_ref="prd_search")
    if limits.within_limits:
        result = await my_tool(customer_ref="cus_123")
```

---

## Quickstart

```bash
pip install solvapay-python
export SOLVAPAY_SECRET_KEY=sk_...
```

```python
from solvapay import SolvaPay

sv = SolvaPay()

# Resource-namespace API (v0.8+)
customer_ref = sv.customers.ensure("user_alice")
session = sv.checkout.create_session(customer_ref=customer_ref, product_ref="prd_0QKI8NHF")
print(session.checkout_url)

limits = sv.limits.check(customer_ref=customer_ref, product_ref="prd_0QKI8NHF")
if limits.within_limits:
    sv.usage.track(customer_ref=customer_ref, product_ref="prd_0QKI8NHF",
                   meter_name="requests", units=1.0)
```

---

## Stable API

| Namespace | Sync methods | Async methods |
|-----------|-------------|---------------|
| `sv.customers` | `ensure`, `get`, `update`, `balance` | `aensure`, `aget`, `aupdate`, `abalance` |
| `sv.checkout` | `create_session` | `acreate_session` |
| `sv.limits` | `check` | `acheck` |
| `sv.purchases` | `cancel`, `reactivate` | `acancel`, `areactivate` |
| `sv.usage` | `track` | `atrack` |
| `sv.products` | `list`, `get`, `create`, `delete`, `clone` | `a` prefix on each |
| `sv.plans` | `list`, `create`, `update`, `delete` | `a` prefix on each |
| `sv.merchant` | `get`, `get_platform_config` | `aget`, `aget_platform_config` |

---

## Errors and retries

```python
from solvapay import AuthenticationError, RateLimitError, SolvaPayError

try:
    sv.customers.ensure("cus_123")
except AuthenticationError:
    print("Check your API key")
except RateLimitError as e:
    print(f"Rate limited — retry after {e.retry_after}s")
except SolvaPayError as e:
    print(f"SDK error: {e}")
```

No built-in retries by design. Layer `tenacity` manually; `solvapay[retry]` RetryTransport coming v0.9.

---

## Webhooks

```python
from solvapay.webhooks import WebhookPipeline

pipeline = WebhookPipeline(
    [os.environ["SOLVAPAY_WEBHOOK_SECRET"]],
    max_clock_skew_seconds=300,   # TWO knobs (HLD V1.7)
    replay_ttl_seconds=600,
)

envelope = pipeline.process(body=request.body, signature=request.headers["sv-signature"])
print(envelope.event["type"])
```

---

## Paywall decorator

```python
from solvapay.paywall import require, PaywallRequired

@require(product="prd_0QKI8NHF", client=sv)
def run_query(*, customer_ref: str, query: str) -> str:
    return expensive_query(query)

try:
    result = run_query(customer_ref="cus_123", query="hello")
except PaywallRequired as e:
    print(f"Upgrade at: {e.checkout_url}")
    if e.checkout_mint_error:
        print(f"Mint failed: {e.checkout_mint_error}")
```

---

## Migrating from v0.7.x flat API

Flat methods still work but emit `DeprecationWarning`. Removed in v2.0.

| v0.7.x | v0.8+ |
|--------|-------|
| `sv.ensure_customer(ref)` | `sv.customers.ensure(ref)` |
| `sv.get_customer(ref)` | `sv.customers.get(ref)` |
| `sv.check_limits(...)` | `sv.limits.check(...)` |
| `sv.track_usage(...)` | `sv.usage.track(...)` |
| `sv.create_checkout_session(...)` | `sv.checkout.create_session(...)` |
| `sv.cancel_purchase(ref)` | `sv.purchases.cancel(ref)` |
| `sv.reactivate_purchase(ref)` | `sv.purchases.reactivate(ref)` |
| `sv.get_customer_balance(ref)` | `sv.customers.balance(ref)` |
| `sv.list_products()` | `sv.products.list()` |
| `sv.create_plan(prd, ...)` | `sv.plans.create(prd, ...)` |
| `sv.get_merchant()` | `sv.merchant.get()` |

---

## Installation

```bash
pip install solvapay-python                   # core
pip install 'solvapay-python[mcp]'            # + FastMCP adapter
pip install 'solvapay-python[langchain]'      # + LangChain adapter
pip install 'solvapay-python[fastapi]'        # + FastAPI webhook router
```

## Environment variables

| Variable | Required | Default |
|----------|----------|---------|
| `SOLVAPAY_SECRET_KEY` | Yes | — |
| `SOLVAPAY_API_BASE_URL` | No | `https://api.solvapay.com` |
| `SOLVAPAY_WEBHOOK_SECRET` | For webhooks | — |

---

## Examples

| Path | What |
|------|------|
| `examples/multi-framework-paywall/` | One tool → MCP + LangChain + async (v0.8 moat demo) |
| `examples/marketplace/` | Streamlit AI-agent marketplace with real SolvaPay sandbox |
| `examples/fastmcp-paywall/` | FastMCP server gated by `@paywall.require` |
| `examples/langchain-paywall/` | LangChain agent with `monetize_tool` |

---

## Status

**v0.8.0** — V1 architecture spine + AI-agent moat + governance scaffold.  
Community SDK, not official. Proposal: [solvapay/solvapay-sdk#187](https://github.com/solvapay/solvapay-sdk/issues/187).
