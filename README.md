# solvapay-python

[![PyPI](https://img.shields.io/pypi/v/solvapay-python)](https://pypi.org/project/solvapay-python/)

Community Python SDK for [SolvaPay](https://solvapay.com) — payment rails for the agentic economy.

> **Status:** v0.7.2, community-maintained. Available on PyPI. Pending official adoption.
> Mirrors the most-used surface of [@solvapay/core](https://github.com/solvapay/solvapay-sdk).

Python is the dominant language for agent frameworks (LangChain, FastMCP, CrewAI, AutoGen). SolvaPay's official SDK is TypeScript-only. This SDK brings first-class Python support so agent developers can gate tools behind paywalls without switching ecosystems.

> **New in v0.7.2:** Async resource leak fix in `@paywall.require_async` — `AsyncSolvaPay` now properly closed when owned by the decorator. Example dep fixes.
> **v0.7.1:** Full error hierarchy (`AuthenticationError`, `NotFoundError`, `RateLimitError`, `APIConnectionError`, `APITimeoutError`), idempotency keys on all mutating ops, `py.typed` PEP 561 marker, structured HTTP logging.
> **New in v0.7.0:** Real-API alignment (wire-format fixes), `paywall_state.gate()` enrichment helper, marketplace Streamlit demo.
> **v0.6:** Admin endpoints (products, plans, merchant, platform config). Published to PyPI.
> **v0.5:** Paywall state classifier (`paywall_state` module) and LangChain `monetize_tool` decorator — gate any LangChain tool behind a SolvaPay paywall with one line.
> **v0.4:** Async client (`AsyncSolvaPay`), lifecycle ops, typed webhook events.

## Install

```bash
pip install solvapay-python
# with optional extras:
pip install solvapay-python[langchain]
pip install solvapay-python[fastapi]
```

## Quickstart

**Sync:**
```python
from solvapay import SolvaPay

sv = SolvaPay()  # reads SOLVAPAY_SECRET_KEY from env

customer_ref = sv.ensure_customer("user_42", email="alice@example.com")
limits = sv.check_limits(customer_ref=customer_ref, product_ref="prd_0QKI8NHF")
if not limits.within_limits:
    print("Upgrade needed:", limits.checkout_url)

session = sv.create_checkout_session(
    customer_ref=customer_ref,
    product_ref="prd_0QKI8NHF",
    return_url="https://your-app.com/done",
)
print(session.checkout_url)
```

**Async:**
```python
import asyncio
from solvapay import AsyncSolvaPay

async def main() -> None:
    async with AsyncSolvaPay() as sv:
        customer_ref = await sv.ensure_customer("user_42", email="alice@example.com")
        limits = await sv.check_limits(customer_ref=customer_ref, product_ref="prd_0QKI8NHF")
        if not limits.within_limits:
            print("Upgrade needed:", limits.checkout_url)
            return
        session = await sv.create_checkout_session(
            customer_ref=customer_ref,
            product_ref="prd_0QKI8NHF",
        )
        print(session.checkout_url)

asyncio.run(main())
```

## Ecosystem integrations

### LangChain

Gate any LangChain tool with `monetize_tool`:

```python
from solvapay.langchain import monetize_tool
from langchain_core.tools import Tool

raw = Tool.from_function(name="search", func=do_search, description="Search the web.")
paid = monetize_tool(raw, product="prd_0QKI8NHF")
```

When the customer is over-limit the tool returns a structured dict with `checkout_url` — the agent surfaces it to the user instead of raising an exception.

```bash
pip install solvapay-python[langchain]
```

See [`examples/langchain-paywall/`](examples/langchain-paywall/) for a full agent example.

### FastMCP

See [`examples/fastmcp-paywall/`](examples/fastmcp-paywall/) for a FastMCP server with two paywalled tools, ready to plug into Claude Desktop.

### FastAPI

Use `webhook_router` to mount a verified webhook endpoint:

```python
from solvapay.fastapi import webhook_router
app.include_router(webhook_router(secret=os.environ["SOLVAPAY_WEBHOOK_SECRET"], on_event=handle))
```

```bash
pip install solvapay-python[fastapi]
```

## Paywall state classifier

`solvapay.paywall_state` maps a `LimitResponse` to a structured recovery action:

```python
from solvapay.paywall_state import decide

limits = sv.check_limits(customer_ref="cus_123", product_ref="prd_xyz")
if not limits.within_limits:
    d = decide(limits)
    print(d.state)        # PaywallState.UPGRADE_REQUIRED
    print(d.message)      # "You don't have an active plan..."
    print(d.recovery_tool)  # "upgrade"
    print(d.checkout_url)   # "https://solvapay.com/c/..."
```

For real-API calls use `gate()` instead — it enriches the bare `/v1/sdk/limits` response (which has no `plan` or `checkout_url`) in one call:

```python
from solvapay.paywall_state import gate

decision = gate(sv, customer_ref="cus_x", product_ref="prd_y")
# decision.state        — PaywallState.UPGRADE_REQUIRED (etc)
# decision.checkout_url — minted via create_checkout_session if needed
# decision.message      — TS-style copy with URL inlined
```

## Error handling

v0.7.1 ships a structured exception hierarchy under `SolvaPayError`:

```python
import time
from solvapay import (
    SolvaPayError,        # catch-all
    APIError,             # base for all HTTP errors — has .status_code, .request_id
    AuthenticationError,  # 401
    NotFoundError,        # 404
    RateLimitError,       # 429 — adds .retry_after
    APIConnectionError,   # network failure
    APITimeoutError,      # request timeout
)

try:
    sv.get_customer("cus_missing")
except NotFoundError as e:
    print(e.status_code, e.request_id)
except RateLimitError as e:
    time.sleep(float(e.retry_after or 1))
except SolvaPayError:
    raise
```

Use `except SolvaPayError` as the catch-all. Prefer specific subclasses over checking `.status_code`.

## Idempotency keys

All mutating ops accept an optional `idempotency_key` to make retries safe:

```python
from solvapay.idempotency import from_payload

key = from_payload("checkout", customer_ref, product_ref)
session = sv.create_checkout_session(
    customer_ref=customer_ref,
    product_ref="prd_xyz",
    idempotency_key=key,
)
```

`from_payload(*parts)` hashes its args to a 32-hex-char deterministic key. Pass the same key on retry — SolvaPay deduplicates server-side.

## Examples

| Path | What it shows |
|---|---|
| [`examples/fastmcp-paywall/`](examples/fastmcp-paywall/) | FastMCP server with two paywalled tools. Demo for `@paywall.require` + MCP. |
| [`examples/langchain-paywall/`](examples/langchain-paywall/) | LangChain agent with `monetize_tool`. Shows paywall response in agent trace. |
| [`examples/marketplace/`](examples/marketplace/) | Streamlit demo — paywalled AI-agent marketplace. Real sandbox, real Gemini LLM, two demo customers (one subscribed, one free tier). Shows `paywall_state.gate()` in action. |

## TS ↔ Python parity

```typescript
// TypeScript (@solvapay/core)
const sv = createSolvaPay();
const session = await sv.createCheckoutSession({
  customerRef: "cus_123",
  productRef: "prd_0QKI8NHF",
});
```

```python
# Python (solvapay-python)
sv = SolvaPay()
session = sv.create_checkout_session(
    customer_ref="cus_123",
    product_ref="prd_0QKI8NHF",
)
```

## Supported methods

**Core:**

| Python | TypeScript equivalent | Description |
|---|---|---|
| `create_checkout_session` | `createCheckoutSession` | Hosted checkout URL |
| `ensure_customer` | `ensureCustomer` | Idempotent customer upsert |
| `get_customer` | `getCustomer` | Fetch customer by ref / email |
| `check_limits` | `checkLimits` | Usage / purchase limit check |
| `verify_webhook` | `verifyWebhook` | HMAC-SHA256 signature verification |

**Lifecycle (new in v0.4):**

| Python | Verb + path | Description |
|---|---|---|
| `track_usage` | `POST /v1/sdk/usages` | Record metered usage |
| `update_customer` | `PATCH /v1/sdk/customers/{ref}` | Update customer email / name |
| `get_customer_balance` | `GET /v1/sdk/customers/{ref}/balance` | Credit balance |
| `cancel_purchase` | `POST /v1/sdk/purchases/{ref}/cancel` | Cancel a subscription |
| `reactivate_purchase` | `POST /v1/sdk/purchases/{ref}/reactivate` | Reactivate cancelled purchase |

**Admin (new in v0.6):**

| Python | Verb + path | Description |
|---|---|---|
| `list_products` | `GET /v1/sdk/products` | List all products |
| `get_product` | `GET /v1/sdk/products/{ref}` | Fetch product |
| `create_product` | `POST /v1/sdk/products` | Create product |
| `delete_product` | `DELETE /v1/sdk/products/{ref}` | Delete product |
| `clone_product` | `POST /v1/sdk/products/{ref}/clone` | Clone product |
| `list_plans` | `GET /v1/sdk/products/{ref}/plans` | List plans |
| `create_plan` | `POST /v1/sdk/products/{ref}/plans` | Create plan |
| `update_plan` | `PUT /v1/sdk/products/{ref}/plans/{ref}` | Update plan |
| `delete_plan` | `DELETE /v1/sdk/products/{ref}/plans/{ref}` | Delete plan |
| `get_merchant` | `GET /v1/sdk/merchant` | Merchant info |
| `get_platform_config` | `GET /v1/sdk/platform-config` | Platform config |

All methods available on both `SolvaPay` (sync) and `AsyncSolvaPay` (async).

## Webhook handler (FastAPI)

```python
from fastapi import FastAPI, HTTPException, Request
from solvapay import SolvaPayError
from solvapay.webhooks import verify_webhook
import os

app = FastAPI()

@app.post("/webhooks/solvapay")
async def handle_webhook(request: Request) -> dict:
    body = (await request.body()).decode()
    sig = request.headers.get("sv-signature", "")
    try:
        event = verify_webhook(
            body=body,
            signature=sig,
            secret=os.environ["SOLVAPAY_WEBHOOK_SECRET"],
        )
    except SolvaPayError as exc:
        raise HTTPException(401, str(exc))
    # Option A: dict (default)
    if event["type"] == "purchase.created":
        ...  # grant access

    # Option B: typed discriminated union (new in v0.4)
    from solvapay import WebhookEvent, PurchaseCreated
    from pydantic import TypeAdapter
    typed = TypeAdapter(WebhookEvent).validate_python(event)
    if isinstance(typed, PurchaseCreated):
        ...  # typed access to typed.data, typed.id, etc.

    return {"received": True}
```

> **Important:** use `await request.body()` (raw bytes), not `await request.json()`.
> Re-serialising JSON changes whitespace and breaks the HMAC signature.

## Environment variables

| Variable | Purpose |
|---|---|
| `SOLVAPAY_SECRET_KEY` | API secret key (required) |
| `SOLVAPAY_API_BASE_URL` | Override API base URL (optional) |
| `SOLVAPAY_WEBHOOK_SECRET` | Webhook signing secret (required for `verify_webhook`) |

## Non-features

- **No retries** — add your own retry logic or use `tenacity`
- **No pagination** — not needed for current endpoints

## Roadmap

- v0.1 — sync client, hosted checkout, customers, limits, webhooks ✅
- v0.2 — `@paywall.require` decorator, FastAPI webhook router ✅
- v0.3 — FastMCP paywall demo (`examples/fastmcp-paywall/`) ✅
- v0.4 — async client (`AsyncSolvaPay`), lifecycle ops, typed webhook events ✅
- v0.5 — paywall state classifier, LangChain `monetize_tool` decorator ✅
- v0.6 — admin endpoints (products, plans, merchant, platform config), PyPI publish ✅
- v0.7.0 — real-API wire-format fixes, `paywall_state.gate()`, marketplace demo ✅
- v0.7.1 — structured error hierarchy, idempotency keys, `py.typed`, structured logging ✅
- v0.7.2 — async resource leak fix (`require_async`), example dep fixes ✅

## Contributing

```bash
git clone https://github.com/dhruv-sanan/solvapay-python
cd solvapay-python
uv sync
uv run pytest
```

Open a PR — all contributions welcome.

## License

MIT
