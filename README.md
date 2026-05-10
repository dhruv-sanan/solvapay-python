# solvapay-python

Community Python SDK for [SolvaPay](https://solvapay.com) — payment rails for the agentic economy.

> **Status:** v0.1, community-maintained. Pending official adoption.
> Mirrors the most-used surface of [@solvapay/core](https://github.com/solvapay/solvapay-sdk).

Python is the dominant language for agent frameworks (LangChain, FastMCP, CrewAI, AutoGen). SolvaPay's official SDK is TypeScript-only. This SDK brings first-class Python support so agent developers can gate tools behind paywalls without switching ecosystems.

## Install

```bash
pip install git+https://github.com/dhruv-sanan/solvapay-python
```

## Quickstart

```python
import os
from solvapay import SolvaPay

sv = SolvaPay()  # reads SOLVAPAY_SECRET_KEY from env

# Ensure customer exists (idempotent)
customer_ref = sv.ensure_customer("user_42", email="alice@example.com")

# Check usage limits before serving
limits = sv.check_limits(customer_ref=customer_ref, product_ref="prd_0QKI8NHF")
if not limits.within_limits:
    print("Upgrade needed:", limits.checkout_url)

# Create a hosted checkout session
session = sv.create_checkout_session(
    customer_ref=customer_ref,
    product_ref="prd_0QKI8NHF",
    return_url="https://your-app.com/done",
)
print(session.checkout_url)
```

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

| Python | TypeScript equivalent | Description |
|---|---|---|
| `create_checkout_session` | `createCheckoutSession` | Hosted checkout URL |
| `ensure_customer` | `ensureCustomer` | Idempotent customer upsert |
| `get_customer` | `getCustomer` | Fetch customer by ref / email |
| `check_limits` | `checkLimits` | Usage / purchase limit check |
| `verify_webhook` | `verifyWebhook` | HMAC-SHA256 signature verification |

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
    if event["type"] == "purchase.created":
        ...  # grant access
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

## Non-features (v0.1)

- **No retries** — add your own retry logic or use `tenacity`
- **Sync only** — async client planned for v0.2
- **No pagination** — not needed for v0.1 endpoints

## Roadmap

- v0.1 — sync client, hosted checkout, customers, limits, webhooks ✅
- v0.2 — async client, `@paywall.require` decorator, FastAPI helper, LangChain tool

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
