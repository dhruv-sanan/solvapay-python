# solvapay-python

Community Python SDK for [SolvaPay](https://solvapay.com) — payment rails for the agentic economy.

> **Status:** v0.1, community-maintained. Pending official adoption.
> Mirrors the most-used surface of [@solvapay/core](https://github.com/solvapay/solvapay-sdk).

## Install

```bash
pip install git+https://github.com/dhruv-sanan/solvapay-python
```

## Quickstart

```python
from solvapay import SolvaPay

sv = SolvaPay()  # reads SOLVAPAY_SECRET_KEY from env

session = sv.create_checkout_session(
    customer_ref="cus_123",
    product_ref="prd_0QKI8NHF",
    return_url="https://your-app.com/done",
)
print(session.checkout_url)
```

## TS ↔ Python parity

```typescript
// TypeScript
const sv = createSolvaPay();
const session = await sv.createCheckoutSession({
  customerRef: "cus_123",
  productRef: "prd_0QKI8NHF",
});
```

```python
# Python
sv = SolvaPay()
session = sv.create_checkout_session(
    customer_ref="cus_123",
    product_ref="prd_0QKI8NHF",
)
```

## Roadmap

- v0.1 — sync client, hosted checkout, customers, limits, webhooks
- v0.2 — async client, `@paywall.require` decorator, FastAPI helper, LangChain tool

## License

MIT
