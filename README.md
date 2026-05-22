# solvapay-python

Community Python SDK for [SolvaPay](https://solvapay.com) — agentic payment rails.  
`pip install solvapay-python` · Python 3.10+ · Fully typed (py.typed) · [PyPI](https://pypi.org/project/solvapay-python/)

[![CI](https://github.com/dhruv-sanan/solvapay-python/actions/workflows/ci.yml/badge.svg)](https://github.com/dhruv-sanan/solvapay-python/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/solvapay-python.svg)](https://pypi.org/project/solvapay-python/)

---

## One tool. Three runtimes. One paywall.

`@payable_tool` stamps a function with payment metadata once. Any framework reads it — no per-framework wiring.

```python
# Define once
from solvapay.adapters.mcp import payable_tool

@payable_tool(product="prd_search")
def web_search(*, customer_ref: str, query: str) -> list[str]:
    """Search the web."""
    return do_real_search(query)
```

```python
# Run on MCP (Claude Desktop / Claude Code)
from solvapay.adapters.mcp import register_payable_tool_fastmcp
from fastmcp import FastMCP

mcp = FastMCP("My App")
register_payable_tool_fastmcp(mcp, web_search)
mcp.run()
```

```python
# Run on LangChain
from solvapay.adapters.langchain import monetize_tool

paid = monetize_tool(web_search, product="prd_search")
# Blocked callers get {"paywall_required": True, "checkout_url": "..."}
```

```python
# Run raw async
async with AsyncSolvaPay() as sv:
    limits = await sv.limits.acheck(customer_ref="cus_123", product_ref="prd_search")
    if limits.within_limits:
        result = await web_search(customer_ref="cus_123", query="hello")
```

`pip install 'solvapay-python[mcp]'` · `pip install 'solvapay-python[langchain]'`

---

## Quickstart

```bash
pip install solvapay-python
export SOLVAPAY_SECRET_KEY=sk_...
```

```python
from solvapay import SolvaPay

sv = SolvaPay()

# Ensure customer exists
customer_ref = sv.customers.ensure("user_alice")

# Create checkout session
session = sv.checkout.create_session(customer_ref=customer_ref, product_ref="prd_0QKI8NHF")
print(session.checkout_url)

# Check limits and track usage
limits = sv.limits.check(customer_ref=customer_ref, product_ref="prd_0QKI8NHF")
if limits.within_limits:
    sv.usage.track(
        customer_ref=customer_ref,
        product_ref="prd_0QKI8NHF",
        meter_name="requests",
        units=1.0,
        idempotency_key="req_abc123",   # idempotent — safe to retry
    )
```

---

## Stable API

| Namespace | Sync | Async |
|-----------|------|-------|
| `sv.customers` | `ensure`, `get`, `update`, `balance` | `aensure`, `aget`, `aupdate`, `abalance` |
| `sv.checkout` | `create_session` | `acreate_session` |
| `sv.limits` | `check` | `acheck` |
| `sv.purchases` | `cancel`, `reactivate` | `acancel`, `areactivate` |
| `sv.usage` | `track` | `atrack` |
| `sv.products` | `list`, `get`, `create`, `delete`, `clone` | `a` prefix on each |
| `sv.plans` | `list`, `create`, `update`, `delete` | `a` prefix on each |
| `sv.merchant` | `get`, `get_platform_config` | `aget`, `aget_platform_config` |

---

## Idempotency

All mutating ops accept `idempotency_key`. Use `solvapay.idempotency.from_payload` to derive deterministic keys from request content:

```python
from solvapay.idempotency import from_payload

key = from_payload("track_usage", customer_ref, product_ref, "requests", units)
sv.usage.track(..., idempotency_key=key)   # retry-safe
```

Retried POSTs **must reuse the same key**. Key should change only when the logical request changes.

---

## Errors and retries

```python
from solvapay import (
    AuthenticationError, PermissionError, NotFoundError,
    RateLimitError, InvalidRequestError, APIServerError,
    APIConnectionError, APITimeoutError, SolvaPayError,
)

try:
    sv.customers.ensure("cus_123")
except AuthenticationError:
    ...  # 401 — bad key
except RateLimitError as e:
    ...  # 429 — retry after e.retry_after seconds
except APIConnectionError:
    ...  # network failure
except APITimeoutError:
    ...  # request timed out (default 30s)
except SolvaPayError as e:
    ...  # catch-all
```

No built-in retries by design. Layer `tenacity` manually. `solvapay[retry]` RetryTransport ships in v0.9.

---

## Webhooks

```python
import os
from solvapay.webhooks import WebhookPipeline

pipeline = WebhookPipeline(
    [os.environ["SOLVAPAY_WEBHOOK_SECRET"]],
    max_clock_skew_seconds=300,
    replay_ttl_seconds=600,
)

envelope = pipeline.process(body=request.body, signature=request.headers["sv-signature"])
```

**Typed events** — discriminated union over 13 event types:

```python
from solvapay import WebhookEvent, PurchaseCreated, PaymentSucceeded
from pydantic import TypeAdapter

event = TypeAdapter(WebhookEvent).validate_python(envelope.event)

match event:
    case PurchaseCreated():
        print(f"New purchase: {event.data['purchaseRef']}")
    case PaymentSucceeded():
        print(f"Payment: {event.data['amount']}")
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
        print(f"Could not auto-mint checkout URL: {e.checkout_mint_error}")
```

Async version: `@require_async`. For MCP/LangChain: `@payable_tool` (see above).

---

## Async

`AsyncSolvaPay` is the supported async pattern. Always use `async with` — it guarantees `aclose()`:

```python
from solvapay import AsyncSolvaPay

async with AsyncSolvaPay() as sv:
    customer_ref = await sv.customers.aensure("user_alice")
    limits = await sv.limits.acheck(customer_ref=customer_ref, product_ref="prd_0QKI8NHF")
    if limits.within_limits:
        await sv.usage.atrack(
            customer_ref=customer_ref,
            product_ref="prd_0QKI8NHF",
            meter_name="requests",
            units=1.0,
        )
```

---

## Migrating from v0.7.x

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
pip install 'solvapay-python[mcp]'            # + FastMCP adapter (FastMCP ≥0.4)
pip install 'solvapay-python[langchain]'      # + LangChain adapter (langchain-core ≥0.3)
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
| `examples/multi-framework-paywall/` | One `@payable_tool` → FastMCP + LangChain + raw async |
| `examples/marketplace/` | Streamlit AI-agent marketplace — real SolvaPay sandbox + Gemini LLM |
| `examples/fastmcp-paywall/` | FastMCP server gated by `@paywall.require` |
| `examples/langchain-paywall/` | LangChain agent with `monetize_tool` |

---

## Roadmap

| Version | Theme |
|---------|-------|
| v0.8 ✅ | V1 architecture spine — Transport kernel, OpSpec registry, paywall/webhook packages, `@payable_tool`, stability manifest, layer DAG CI gate |
| v0.9 | Production polish — API-version pinning, idempotency TTL, `RetryTransport`, `RecordingTransport`, contract tests, lint automation, doc site (MkDocs Material), supply-chain hygiene |
| v1.0 | Gated on founder signal — OpenAPI-generated models, full secret rotation, production hardening |

---

## Status

**v0.8.0** — V1 architecture spine + AI-agent moat. `mypy --strict` clean (43 files). 261 tests. 89% line coverage.  
Community SDK, not official. Proposal: [solvapay/solvapay-sdk#187](https://github.com/solvapay/solvapay-sdk/issues/187).
