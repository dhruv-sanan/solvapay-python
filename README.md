# solvapay-python

[![PyPI version](https://img.shields.io/pypi/v/solvapay-python.svg)](https://pypi.org/project/solvapay-python/)
[![Python](https://img.shields.io/pypi/pyversions/solvapay-python.svg)](https://pypi.org/project/solvapay-python/)
[![CI](https://github.com/dhruv-sanan/solvapay-python/actions/workflows/ci.yml/badge.svg)](https://github.com/dhruv-sanan/solvapay-python/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Typed](https://img.shields.io/badge/typing-py.typed-informational.svg)](https://peps.python.org/pep-0561/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Tests](https://img.shields.io/badge/tests-142%20passing-brightgreen.svg)](https://github.com/dhruv-sanan/solvapay-python/actions/workflows/ci.yml)

**Payment infrastructure for Python AI agents.**

Gate any function, MCP tool, or LangChain agent behind a [SolvaPay](https://solvapay.com) paywall
with one decorator. Fully async. Verified against the live API. `mypy --strict` clean.

> **Community SDK** — v0.7.2, MIT, available on PyPI as `solvapay-python`.  
> Mirrors the full surface of [@solvapay/core](https://github.com/solvapay/solvapay-sdk).  
> Potential official adoption pending — the `solvapay` PyPI namespace is held for the founders.

---

## Current Status

Production-oriented community SDK under active development. The API surface covers the full
`@solvapay/core` operation set, is wire-verified against the real SolvaPay sandbox, and ships
with 142 tests, `mypy --strict` clean source, and `py.typed` for downstream type checking.

Stability guarantees follow [SemVer](https://semver.org/) for the public surface in
`solvapay.__init__`. Private modules (`_http`, `_config`, `_async_client`) may change between
minor versions. v1.0 stability contract — including a formal deprecation policy and API freeze —
is gated on official SolvaPay adoption. Until then, treat this as pre-v1: solid for production
use, with the understanding that minor versions may introduce breaking changes to non-public APIs.

---

## Why this SDK exists

Python is the dominant language for AI agent frameworks — FastMCP, LangChain, CrewAI, AutoGen,
and raw Anthropic/OpenAI tool-use all live in Python. SolvaPay's official SDK is TypeScript-only.

This SDK fills that gap: a Python-native, async-first, fully typed client that integrates with every
major Python AI framework. If you're building agents that should charge per tool call, gate premium
capabilities behind subscriptions, or track per-customer usage — this is the SDK.

![Agent Marketplace demo — SolvaPay Python SDK](https://raw.githubusercontent.com/dhruv-sanan/solvapay-python/main/assets/agent-marketplace.png)

*Paywalled AI-agent marketplace built with this SDK. Real SolvaPay sandbox. Real Gemini LLM. Two
demo customers — one subscribed (passes), one free tier (blocked with checkout URL). Source in
[`examples/marketplace/`](https://github.com/dhruv-sanan/solvapay-python/tree/main/examples/marketplace).*

---

## Install

```bash
pip install solvapay-python                      # core: sync + async client, webhooks, paywall
pip install "solvapay-python[langchain]"         # + LangChain monetize_tool decorator
pip install "solvapay-python[fastapi]"           # + FastAPI webhook router
```

**Requires:** Python ≥ 3.10, Pydantic v2, httpx

---

## Quickstart

### MCP tool paywall (FastMCP)

Gate a FastMCP tool behind a SolvaPay paywall in three lines:

```python
# server.py
import os
from fastmcp import FastMCP
from solvapay import SolvaPay
from solvapay.paywall import paywall

mcp = FastMCP("my-agent")
sv  = SolvaPay(api_key=os.environ["SOLVAPAY_SECRET_KEY"])

@mcp.tool()
@paywall.require(product="prd_xyz", client=sv)
def search_web(*, customer_ref: str, query: str) -> str:
    """Search the web. Requires an active SolvaPay subscription."""
    return do_actual_search(query)
```

When a customer hits their limit, `PaywallRequired` is raised with a ready-to-use `checkout_url`.
See [`examples/fastmcp-paywall/`](https://github.com/dhruv-sanan/solvapay-python/tree/main/examples/fastmcp-paywall)
for the full runnable demo (includes Claude Desktop config).

### LangChain tool paywall

```python
from solvapay.langchain import monetize_tool
from langchain_core.tools import Tool

raw  = Tool.from_function(name="search", func=do_search, description="Search the web.")
paid = monetize_tool(raw, product="prd_xyz")
# Over-limit: returns structured dict with checkout_url — agent surfaces it to the user naturally
```

See [`examples/langchain-paywall/`](https://github.com/dhruv-sanan/solvapay-python/tree/main/examples/langchain-paywall)
for a full ReAct agent that handles the paywall state in its trace.

### Raw sync client

```python
from solvapay import SolvaPay

sv = SolvaPay()  # reads SOLVAPAY_SECRET_KEY from env

customer_ref = sv.ensure_customer("user_42", email="alice@example.com")
session      = sv.create_checkout_session(
    customer_ref=customer_ref,
    product_ref="prd_xyz",
    return_url="https://your-app.com/done",
)
print(session.checkout_url)
```

### Raw async client

Use `async with` — it is the only supported lifecycle pattern. `AsyncSolvaPay` owns an
`httpx.AsyncClient` pool and must be explicitly closed to avoid resource leaks.

```python
from solvapay import AsyncSolvaPay

async with AsyncSolvaPay() as sv:
    customer_ref = await sv.ensure_customer("user_42")
    limits       = await sv.check_limits(customer_ref=customer_ref, product_ref="prd_xyz")
    if not limits.within_limits:
        return limits.checkout_url  # already minted by the decorator
```

---

## AI-Agent Ecosystem

### FastMCP / Model Context Protocol

`@paywall.require` stacks cleanly under `@mcp.tool()` via `functools.wraps` — FastMCP introspects
the underlying signature and docstring, not the wrapper. No schema pollution.

```python
@mcp.tool()
@paywall.require(product="prd_xyz", plan="pln_pro", client=sv)
def analyze_document(*, customer_ref: str, text: str) -> str: ...
```

Upcoming in **v0.8**: `solvapay.mcp` — a framework-neutral `@payable_tool` decorator and
`payable_tool_schema()` that generates a single Pydantic-derived JSON Schema usable across
FastMCP, LangChain `args_schema`, OpenAI function-calling, and Anthropic tool_use simultaneously.

### LangChain

`monetize_tool` wraps any `BaseTool` subclass. Returns a structured dict on gate-hit instead of
raising — LangChain agents handle dicts gracefully without corrupting the agent trace.

```python
from solvapay.langchain import monetize_tool

paid = monetize_tool(tool, product="prd_xyz", customer_ref_arg="customer_ref")
# On block: {"paywall_required": True, "state": "UPGRADE_REQUIRED",
#            "message": "...", "checkout_url": "https://solvapay.com/c/..."}
```

Install: `pip install "solvapay-python[langchain]"`

### CrewAI

```python
from crewai import tool as crewai_tool
from solvapay.paywall import paywall

@crewai_tool("Search Web")
@paywall.require(product="prd_xyz", client=sv)
def search_web(*, customer_ref: str, query: str) -> str:
    return do_search(query)
```

### AutoGen / raw async

```python
from solvapay import AsyncSolvaPay
from solvapay.paywall_state import gate, PaywallState

async with AsyncSolvaPay() as sv:
    decision = await gate(sv, customer_ref=customer_ref, product_ref="prd_xyz")
    if decision.state != PaywallState.OK:
        yield f"Upgrade required: {decision.checkout_url}"
        return
    # proceed with LLM call
```

---

## Paywall State Classifier

`solvapay.paywall_state` maps a `LimitResponse` to a structured recovery action. The state machine
mirrors `@solvapay/core`'s `paywall-state.ts` branching exactly.

```python
from solvapay.paywall_state import decide, PaywallState

limits = sv.check_limits(customer_ref="cus_123", product_ref="prd_xyz")
if not limits.within_limits:
    d = decide(limits)
    print(d.state)          # PaywallState.UPGRADE_REQUIRED
    print(d.message)        # "You don't have an active plan..."
    print(d.recovery_tool)  # "upgrade"
    print(d.checkout_url)   # "https://solvapay.com/c/..."
```

**States:**

| State | Meaning | Recovery |
|---|---|---|
| `OK` | Within limits | — |
| `ACTIVATION_REQUIRED` | No active plan | Subscribe |
| `UPGRADE_REQUIRED` | Plan cap hit | Upgrade plan |
| `TOPUP_REQUIRED` | Out of credits | Buy credits |
| `REACTIVATION_REQUIRED` | Cancelled plan | Reactivate |

<details>
<summary><strong>gate()</strong> — enriched one-call helper for real API responses</summary>

The live `/v1/sdk/limits` endpoint returns `{withinLimits, remaining, meterName}` only — no
`plan`, no `checkoutUrl`. Use `gate()` instead of calling `decide()` directly: it enriches the
bare response in one call (mints checkout URL if blocked, reads plan from customer purchases).

```python
from solvapay.paywall_state import gate

decision = gate(sv, customer_ref="cus_x", product_ref="prd_y")
# Internally: check_limits → mint checkout_url if blocked → read plan from purchases
# Always returns GateDecision — never raises.
```

</details>

---

## Production Features

### Structured error hierarchy

Every SDK exception inherits from `SolvaPayError`. The hierarchy mirrors payments-industry
conventions — catch narrow exceptions for recovery, `SolvaPayError` as the catch-all.
`APIError.request_id` captures the `x-request-id` / `x-correlation-id` header for support correlation.

<details>
<summary>Full exception hierarchy + handling example</summary>

```python
from solvapay import (
    SolvaPayError,        # catch-all
    APIError,             # base HTTP error — .status_code, .request_id
    AuthenticationError,  # 401
    NotFoundError,        # 404
    RateLimitError,       # 429 — .retry_after
    InvalidRequestError,  # other 4xx
    APIServerError,       # 5xx
    APIConnectionError,   # network failure
    APITimeoutError,      # request timeout
)

try:
    sv.get_customer("cus_missing")
except NotFoundError as e:
    print(e.request_id)              # x-request-id for support correlation
except RateLimitError as e:
    time.sleep(float(e.retry_after or 1))
except SolvaPayError:
    raise
```

</details>

### Idempotency

All mutating operations accept `idempotency_key`. Pass the same key on retry — SolvaPay
deduplicates server-side. `from_payload(*parts)` generates a deterministic SHA256 key from
stable inputs, safe to reuse across process restarts.

<details>
<summary>from_payload() helper + full example</summary>

```python
from solvapay.idempotency import from_payload

key     = from_payload("checkout", customer_ref, product_ref)  # SHA256 → 32-hex
session = sv.create_checkout_session(
    customer_ref=customer_ref,
    product_ref="prd_xyz",
    idempotency_key=key,
)
# Retry with the same key → same session returned, no duplicate charge
```

Changing the key on retry defeats server-side deduplication — the server sees it as a new request.

</details>

### Structured logging

The SDK logs via `logging.getLogger("solvapay.http")` — INFO on success, WARNING on errors.
It never calls `logging.basicConfig` and never configures root handlers. Your app controls the
log format and destination.

```python
import logging
logging.basicConfig(level=logging.INFO)  # in your app startup, not in the SDK

sv = SolvaPay(logger=logging.getLogger("myapp.payments"))  # optional: inject your own logger
```

API keys are **never** written to logs. The redaction contract is enforced by tests
(`tests/test_redaction.py`).

### Type safety

`solvapay-python` ships a `py.typed` marker (PEP 561). Downstream projects with `mypy --strict`
get fully typed imports — no implicit `Any`. The SDK itself passes `mypy --strict` clean.

---

## Webhook Security

`verify_webhook` implements HMAC-SHA256 signature verification byte-for-byte with the TS SDK.

```python
import os
from solvapay.webhooks import verify_webhook
from solvapay import SolvaPayError

body = (await request.body()).decode()  # raw bytes — do NOT use request.json()
sig  = request.headers.get("sv-signature", "")

try:
    event = verify_webhook(body=body, signature=sig,
                           secret=os.environ["SOLVAPAY_WEBHOOK_SECRET"])
except SolvaPayError:
    raise HTTPException(401)

# Typed events (discriminated union — 13 event types):
from solvapay import WebhookEvent, PurchaseCreated
from pydantic import TypeAdapter
typed = TypeAdapter(WebhookEvent).validate_python(event)
if isinstance(typed, PurchaseCreated):
    grant_access(typed.data.customer_ref)
```

> **Critical:** use `await request.body()` (raw bytes), **not** `request.json()`.  
> Re-serialising JSON reorders keys and breaks the HMAC signature.

**Verification algorithm:**
1. Parse `sv-signature` header: `t={unix_ts},v1={hex_hmac}`
2. Reject if `|now − t| > 300s` (replay protection)
3. Compute `HMAC-SHA256(secret, f"{t}.{body}")` over the **raw** body string
4. `hmac.compare_digest(expected, received)` — constant-time, no timing leaks

**FastAPI one-liner:**

```python
from solvapay.fastapi import webhook_router

app.include_router(
    webhook_router(secret=os.environ["SOLVAPAY_WEBHOOK_SECRET"], on_event=handle_event)
)
```

Install: `pip install "solvapay-python[fastapi]"`

---

## Architecture

<details>
<summary>Module dependency diagram</summary>

```
                  ┌───────────────────────────────┐
                  │      __init__.py (exports)     │
                  └───────────────┬───────────────┘
                                  │
      ┌──────────────┬────────────┼────────────┬──────────────┬──────────────┐
      │              │            │            │              │              │
      ▼              ▼            ▼            ▼              ▼              ▼
  client.py     webhooks.py  paywall.py   fastapi.py  paywall_state.py  langchain.py
      │              │            │            │              ▲              │
      ▼              ▼            ▼            ▼              │              │
  _http.py      exceptions   client +     webhooks +     (pure fn,       client +
      │                      exceptions   exceptions      no HTTP)      paywall_state
      ▼
  _config.py
      │
      ▼
  os.environ
```

`_config.py` and `_http.py` are leaf nodes — they know nothing about higher layers.
`client.py` is the only orchestration point. No circular dependencies. No global state.

</details>

<details>
<summary>Request lifecycle — paywall decorator</summary>

```
caller → decorated_fn(customer_ref=..., **kwargs)
           │
           ▼
    extract customer_ref from kwargs
           │
           ▼
    SolvaPay.check_limits(customer_ref, product_ref, plan_ref)
           │                    │
     within_limits=True         │  within_limits=False
           │                    │
           ▼                    ▼
    fn(*args, **kwargs)    checkout_url present?
    (pass-through)               │           │
                                yes          no
                                 │           │
                                 │           ▼
                                 │    create_checkout_session(...)
                                 │           │
                                 └───────────┘
                                             │
                                             ▼
                                raise PaywallRequired(checkout_url=...)
```

</details>

<details>
<summary>MCP → paywall → checkout flow</summary>

```
MCP Client          FastMCP Server       SolvaPay Decorator      SolvaPay API
(Claude Desktop)
    │                     │                      │                     │
    │──── tool call ──────▶                      │                     │
    │                     │──── check_limits ────▶                     │
    │                     │                      │── POST /limits ─────▶
    │                     │                      │◀── {withinLimits} ──│
    │                     │                      │                     │
    │         ┌───── within_limits=True ─────────┤                     │
    │         │           │                      │                     │
    │         │     execute tool fn              │                     │
    │◀─ result ───────────│                      │                     │
    │                     │                      │                     │
    │         └───── within_limits=False ─────────┤                     │
    │                     │                      │── POST /checkout ───▶
    │                     │                      │◀── {checkoutUrl} ───│
    │◀─ PaywallRequired ──│                      │                     │
    │   {checkout_url}    │                      │                     │
```

</details>

<details>
<summary>Webhook trust boundary</summary>

```
SolvaPay Platform            Internet             Your Server
        │                                              │
        │── POST /webhooks/solvapay                    │
        │   Body: raw JSON                             │
        │   sv-signature: t={ts},v1={hmac}             │
        │─────────────────────────────────────────────▶│
        │                                              │
        │                             verify_webhook() │
        │                         1. parse t + v1      │
        │                         2. |now-t| ≤ 300s    │
        │                         3. HMAC-SHA256(...)  │
        │                         4. compare_digest    │
        │                                              │
        │◀─ 200 OK (valid) ────────────────────────────│
        │◀─ 401 (invalid / replayed) ──────────────────│
```

</details>

---

## Supported Methods

All methods available on both `SolvaPay` (sync) and `AsyncSolvaPay` (async).

**Core:**

| Method | REST | Description |
|---|---|---|
| `create_checkout_session` | `POST /v1/sdk/checkout-sessions` | Hosted checkout URL |
| `ensure_customer` | `GET` then `POST /v1/sdk/customers` | Idempotent upsert |
| `get_customer` | `GET /v1/sdk/customers/{ref}` | Fetch by ref or email |
| `check_limits` | `POST /v1/sdk/limits` | Usage / purchase limit check |
| `verify_webhook` | — | HMAC-SHA256 signature verification |

<details>
<summary><strong>Lifecycle ops</strong> — usage tracking, balance, subscriptions (5 methods)</summary>

| Method | REST | Description |
|---|---|---|
| `track_usage` | `POST /v1/sdk/usages` | Record metered usage |
| `update_customer` | `PATCH /v1/sdk/customers/{ref}` | Update email / name |
| `get_customer_balance` | `GET /v1/sdk/customers/{ref}/balance` | Credit balance |
| `cancel_purchase` | `POST /v1/sdk/purchases/{ref}/cancel` | Cancel subscription |
| `reactivate_purchase` | `POST /v1/sdk/purchases/{ref}/reactivate` | Reactivate |

</details>

<details>
<summary><strong>Admin ops</strong> — products, plans, merchant config (11 methods)</summary>

| Method | REST | Description |
|---|---|---|
| `list_products` / `get_product` | `GET /v1/sdk/products` | Product catalogue |
| `create_product` / `clone_product` / `delete_product` | `POST` / `DELETE` | Product management |
| `list_plans` / `create_plan` / `update_plan` / `delete_plan` | `GET` / `POST` / `PUT` / `DELETE` | Plan management |
| `get_merchant` | `GET /v1/sdk/merchant` | Merchant info |
| `get_platform_config` | `GET /v1/sdk/platform-config` | Platform config |

</details>

**Mutating ops** (`create_*`, `track_usage`, `cancel_*`, `reactivate_*`, `clone_*`) accept
`idempotency_key: str | None = None` for safe retries.

---

## TypeScript Parity

Wire format identical (camelCase JSON). Python surface uses snake_case + keyword-only args —
idiomatic Python, zero config to switch between SDKs.

<details>
<summary>Side-by-side example</summary>

```typescript
// @solvapay/core
const session = await sv.createCheckoutSession({
  customerRef: "cus_123",
  productRef:  "prd_xyz",
});
```

```python
# solvapay-python
session = sv.create_checkout_session(
    customer_ref="cus_123",
    product_ref="prd_xyz",
)
```

</details>

---

## Design Principles

No retries. No global state. No telemetry. No magic config. Type-first, thin transport.

<details>
<summary>All 7 principles</summary>

- **No retries in core.** Retry policy belongs to the caller. Use `tenacity` or the upcoming
  `solvapay[retry]` extra (v0.9). Payment retries are not like HTTP retries — a naively retried
  `POST /checkout-sessions` can charge a customer twice. Safe retry requires idempotency discipline:
  generate a deterministic key with `from_payload(...)` and pass the same key on every attempt.
  The SDK provides the primitive; the retry loop is yours to own.
- **No global state.** No module-level `_default_client` singleton. Each caller constructs
  its own `SolvaPay()`. Safe in multi-tenant and serverless environments.
- **No telemetry.** The SDK never phones home.
- **No magic config.** No auto-loading of `.env` files, `~/.solvapay/config`, or other
  ambient config. All inputs are explicit.
- **Async context manager is the contract.** `async with AsyncSolvaPay() as sv` is the
  supported pattern. `AsyncSolvaPay` constructed outside a context manager will warn on GC
  if the underlying `httpx.AsyncClient` pool is not explicitly closed.
- **Thin transport.** `client.py` orchestrates HTTP + models + config. Zero business logic.
  Decision logic (paywall state, gate enrichment) lives in `paywall_state.py`.
- **Type-first.** `mypy --strict` clean. `py.typed` marker shipped. Pydantic v2 models
  use `extra="ignore"` so new API fields never break parsing.

</details>

---

## Examples

| Path | What it shows |
|---|---|
| [`examples/fastmcp-paywall/`](https://github.com/dhruv-sanan/solvapay-python/tree/main/examples/fastmcp-paywall) | FastMCP server with two `@paywall.require` tools + Claude Desktop config |
| [`examples/langchain-paywall/`](https://github.com/dhruv-sanan/solvapay-python/tree/main/examples/langchain-paywall) | LangChain ReAct agent — `monetize_tool`, paywall state surfaced in agent trace |
| [`examples/marketplace/`](https://github.com/dhruv-sanan/solvapay-python/tree/main/examples/marketplace) | Streamlit demo — paywalled AI-agent marketplace, real SolvaPay sandbox, real Gemini LLM, two demo customers (one subscribed, one free tier) |

---

## Environment Variables

| Variable | Purpose |
|---|---|
| `SOLVAPAY_SECRET_KEY` | API secret key (required) |
| `SOLVAPAY_API_BASE_URL` | Override API base URL (optional, defaults to `https://api.solvapay.com`) |
| `SOLVAPAY_WEBHOOK_SECRET` | Webhook signing secret (required for `verify_webhook`) |

---

## Roadmap

| Version | Theme | Status |
|---|---|---|
| v0.1 | Sync client, checkout, customers, limits, webhooks | ✅ shipped |
| v0.2 | `@paywall.require` decorator, FastAPI webhook router | ✅ shipped |
| v0.3 | FastMCP paywall demo | ✅ shipped |
| v0.4 | `AsyncSolvaPay`, lifecycle ops, typed webhook events | ✅ shipped |
| v0.5 | Paywall state classifier, LangChain `monetize_tool` | ✅ shipped |
| v0.6 | Admin endpoints, PyPI publish | ✅ shipped |
| v0.7.0 | Real-API wire-format fixes, `paywall_state.gate()`, marketplace demo | ✅ shipped |
| v0.7.1 | Structured error hierarchy, idempotency keys, `py.typed`, logging | ✅ shipped |
| v0.7.2 | Async resource leak fix, example dep fixes | ✅ shipped |
| v0.8 | `solvapay.mcp` first-class module, LangChain Protocol refactor, multi-framework demo, governance scaffold | 🔜 next |
| v0.9 | Webhook secret rotation, nonce cache, ASGI/WSGI/Lambda handlers, contract tests, `solvapay[retry]` | 🔜 planned |
| v1.0 | Stability contract — gated on official SolvaPay adoption signal | 🔒 gated |

v1.0 is intentionally gated on official adoption — the `solvapay` PyPI namespace is held for the
founders. This SDK ships as `solvapay-python`; the import surface (`from solvapay import ...`) is
unchanged regardless of distribution name.

---

## Contributing

```bash
git clone https://github.com/dhruv-sanan/solvapay-python
cd solvapay-python
uv sync --all-extras --dev    # install all optional deps + dev tools
uv run pytest                 # 142 tests, should be green
uv run ruff check src tests   # lint
uv run ruff format --check src tests  # format gate (separate from lint)
uv run mypy src               # strict type check
```

**Before opening a PR:**
- Add tests for new behaviour (`@respx.mock` for HTTP paths, direct call for pure functions)
- `ruff format` applied (not just `ruff check` — they are separate gates)
- `mypy --strict` clean on `src/`
- Conventional Commits format (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `ci:`)

All contributions welcome. See [open issues](https://github.com/dhruv-sanan/solvapay-python/issues)
for good first tasks.

---

## License

MIT — see [LICENSE](LICENSE).
