# solvapay-python

[![PyPI](https://img.shields.io/pypi/v/solvapay-python)](https://pypi.org/project/solvapay-python/)

Community Python SDK for [SolvaPay](https://solvapay.com) — payment rails for the agentic economy.

> **Status:** v0.6, community-maintained. Available on PyPI. Pending official adoption.
> Mirrors the most-used surface of [@solvapay/core](https://github.com/solvapay/solvapay-sdk).

Python is the dominant language for agent frameworks (LangChain, FastMCP, CrewAI, AutoGen). SolvaPay's official SDK is TypeScript-only. This SDK brings first-class Python support so agent developers can gate tools behind paywalls without switching ecosystems.

> **New in v0.6:** Admin endpoints (products, plans, merchant, platform config). Published to PyPI.
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

## Examples

| Path | What it shows |
|---|---|
| [`examples/fastmcp-paywall/`](examples/fastmcp-paywall/) | FastMCP server with two paywalled tools. Demo for `@paywall.require` + MCP. |
| [`examples/langchain-paywall/`](examples/langchain-paywall/) | LangChain agent with `monetize_tool`. Shows paywall response in agent trace. |

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
