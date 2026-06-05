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

All mutating ops accept `idempotency_key`. Use `solvapay.idempotency.from_payload` to derive deterministic keys:

```python
from solvapay.idempotency import from_payload

# Default: key includes UTC date — rolls at midnight, bounds replay past server TTL
key = from_payload("track_usage", customer_ref, product_ref, "requests", units)
sv.usage.track(..., idempotency_key=key)   # retry-safe

# Hourly bucket (high-frequency ops)
key = from_payload("charge", customer_ref, time_bucket="hour")

# Pure payload hash — caller manages TTL externally
key = from_payload("idempotent_op", ref, time_bucket=None)
```

Retried POSTs **must reuse the same key**. A bucket roll (midnight / hour boundary) produces a new key — the server treats it as a new request.

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

No built-in retries by default. `solvapay[retry]` ships `RetryTransport` — exponential backoff with jitter, 3 attempts, respects `OpSpec.retry_safety` (won't retry non-idempotent ops without an idempotency key). Or layer `tenacity` manually.

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

**Secret rotation** — pass multiple secrets; primary tried first, secondary on mismatch:

```python
pipeline = WebhookPipeline(["whsec_new...", "whsec_old..."])
```

**Sign a webhook** (testing / outbound fanout):

```python
from solvapay.webhooks import sign_webhook

header = sign_webhook(body=b'{"type":"purchase.created"}', secret="whsec_...")
# → "t=1716470000,v1=abc123..."
```

**ASGI adapter** — mount directly in FastAPI / Starlette / Litestar:

```python
from solvapay.adapters.asgi import webhook_app

app.mount("/webhook", webhook_app(pipeline, on_event=handle))
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
pip install 'solvapay-python[asgi]'           # + raw ASGI webhook adapter (no extra deps)
pip install 'solvapay-python[retry]'          # + RetryTransport (tenacity)
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

## API version pinning

Pin the API version your code was written against — prevents silent breakage when the server evolves:

```python
sv = SolvaPay(api_version="2026-05-22")   # sends Solvapay-Version header
sv = SolvaPay(api_version=None)            # omit header (use server default)
```

Default is `"2026-05-22"` (v0.9 ship date). Bump only on major SDK versions.

---

## Roadmap

| Version | Theme |
|---------|-------|
| v0.8 ✅ | V1 architecture spine — Transport kernel, OpSpec registry, paywall/webhook packages, `@payable_tool`, stability manifest, layer DAG CI gate |
| v0.9 ✅ | Production polish — API-version pinning, idempotency TTL, `RetryTransport`, `RecordingTransport`, ASGI adapter, secret rotation, `sign_webhook`, contract tests, lint automation, MkDocs site, supply-chain hygiene |
| v0.9.1 ✅ | Security & supply-chain quality — PyPI attestations (PEP 740 / Sigstore), CycloneDX SBOM on releases, `bandit` + `osv-scanner` CI, Hypothesis-driven secret-redaction property tests, constant-time `verify_webhook` smoke test, explicit PCI-scope statement |
| v1.0 | Gated on founder signal — OpenAPI-generated models, WSGI/Lambda adapters, V2 planning |

---

## Status

**v0.9.1** — Security & supply-chain quality patch. PyPI uploads now carry PEP 740 attestations (Sigstore-backed via OIDC trusted publishing); each GitHub release ships a CycloneDX SBOM (`sbom.cdx.json`). `mypy --strict` clean (45 files). 302 tests. 87% line / 85% branch coverage.

**Supply chain & security posture:**
- PyPI trusted publishing with PEP 740 attestations (Sigstore)
- CycloneDX 1.6 SBOM attached to every release
- CI runs `bandit -r src/ -lll`, `osv-scanner --lockfile=uv.lock`, and `pip-audit` (cross-DB vuln check) on PR and nightly cron
- Constant-time HMAC comparison (`hmac.compare_digest`) regression-smoked
- Hypothesis-driven property tests assert no API key, hex token, or webhook secret leaks into log output at any level
- Tightened upper bounds on volatile deps (`httpx<0.29`, `pydantic<2.14`, `langchain-core<1.5`)

Community SDK, not official. Proposal: [solvapay/solvapay-sdk#187](https://github.com/solvapay/solvapay-sdk/issues/187).
