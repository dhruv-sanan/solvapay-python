# Agent Marketplace — a real SolvaPay SDK demo

Streamlit marketplace of paywalled AI agents. Every paywall decision hits the
real **SolvaPay sandbox**. Every agent run hits a real **Gemini LLM**.

## What's real

- `solvapay-python` SDK — unmodified, against `https://api.solvapay.com`
  - `check_limits` → real
  - `track_usage` → real (sandbox metering ticks)
  - `get_customer_balance` → real
  - `ensure_customer` → real (bootstraps Customer B on first run)
  - `paywall_state.decide()` → real typed state machine on real responses
  - `@paywall.require` decorator → real, raises `PaywallRequired` from sandbox
- Two real sandbox customers:
  - **Alice** (`SOLVAPAY_DEMO_CUSTOMER_REF`) — pre-existing, subscribed
  - **Bob** (`SOLVAPAY_DEMO_BLOCKED_CUSTOMER_REF`) — created by the app via
    `ensure_customer()` on first boot; no plan assigned → SolvaPay returns
    `withinLimits=false`
- One real product (`SOLVAPAY_PRODUCT_REF`) — all 4 agents bill against it
- Real LLM calls via Google Gemini

## What's "fake"

- The 4 per-agent display prices ($0.02 / $0.05 / $0.10 / $0.03) are cosmetic
  for the marketplace look. Real metering is whatever your SolvaPay product
  config dictates. The sidebar discloses this.

That's it. No HTTP mocking. No fake customers.

## Setup

```bash
pip install -r requirements.txt
pip install -e ../..             # local SDK (editable)
cp .env.example .env             # fill in:
                                 #   SOLVAPAY_SECRET_KEY (sandbox)
                                 #   SOLVAPAY_PRODUCT_REF (your product)
                                 #   SOLVAPAY_DEMO_CUSTOMER_REF (subscribed customer)
                                 #   GEMINI_API_KEY
streamlit run app.py
```

First boot calls `client.ensure_customer(...)` to create Customer B in your
sandbox. Subsequent boots find the same customer (idempotent).

## What the demo shows

1. Alice runs an agent → SDK approves → LLM responds → usage tracked.
2. Switch to Bob → click any agent → SDK blocks → `paywall_state.decide()`
   returns a typed `GateDecision` → UI branches on the enum.
3. The "Show the SDK call" panel under each gated result prints the real
   Python that produced the state — including the real `checkout_url`
   SolvaPay returned. Click it; it opens the real sandbox checkout.

Two integration styles visible side-by-side:

- **Explicit** — Web Researcher / Text Analyst / Image Describer use
  `client.check_limits(...)` + `paywall_state.decide(...)`.
- **Decorator** — Code Reviewer's runner is wrapped with
  `@paywall.require(product=..., customer_ref_arg="customer_ref")`.
  Catches `PaywallRequired` and re-uses the explicit path to populate the
  same typed banner.

## Cost

Each full demo cycle costs <$0.01 in Gemini tokens. SolvaPay sandbox is free.
