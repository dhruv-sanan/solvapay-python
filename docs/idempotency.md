# Idempotency

Idempotency keys prevent duplicate operations when a request is retried after a network failure or timeout.

## Quick start

```python
from solvapay import SolvaPay
from solvapay.idempotency import from_payload

sv = SolvaPay()

key = from_payload("cus_123", "prd_abc", "checkout")
session = sv.checkout.create_session(
    customer_ref="cus_123",
    product_ref="prd_abc",
    idempotency_key=key,
)
```

## `from_payload` — key generation

```python
from solvapay.idempotency import from_payload

key = from_payload(*parts, time_bucket="day")
```

Produces a 32-hex-character SHA-256 key from the given payload parts.

### `time_bucket` parameter

| Value | Behaviour | Use when |
|-------|-----------|----------|
| `"day"` (default) | Appends current UTC date (`2026-05-22`). Key changes at midnight UTC. | Standard checkout / purchase flows |
| `"hour"` | Appends current UTC hour (`2026-05-22T14`). Key changes every hour. | High-frequency operations where 24 h TTL is too wide |
| `None` | Pure payload hash — deterministic across time. | Caller manages TTL externally, or operation has no server-side TTL |

### Retry contract

**Retried POSTs MUST reuse the exact same `idempotency_key` as the original call.**

If the key changes between the original request and the retry, the server treats it as a new request, which can cause duplicate charges or records.

```python
key = from_payload("cus_123", "prd_abc", time_bucket="day")

# Original attempt (may fail with network error)
try:
    session = sv.checkout.create_session(
        customer_ref="cus_123",
        product_ref="prd_abc",
        idempotency_key=key,
    )
except APIConnectionError:
    # Retry — same key, same day → server deduplicates
    session = sv.checkout.create_session(
        customer_ref="cus_123",
        product_ref="prd_abc",
        idempotency_key=key,
    )
```

### Bucket roll

A bucket roll (midnight UTC for `"day"`, hour boundary for `"hour"`) produces a **different key**. The server will treat a request with the new key as a fresh operation. Do not retry across a bucket boundary unless you intend to create a new operation.

## Which operations accept `idempotency_key`?

All mutating `POST` operations accept an optional `idempotency_key` kwarg:

- `sv.checkout.create_session(..., idempotency_key=key)`
- `sv.customers.ensure(..., idempotency_key=key)`
- `sv.usage.track(..., idempotency_key=key)`
- `sv.purchases.cancel(..., idempotency_key=key)`
- `sv.purchases.reactivate(..., idempotency_key=key)`
- `sv.products.create(..., idempotency_key=key)`
- `sv.products.clone(..., idempotency_key=key)`
- `sv.plans.create(..., idempotency_key=key)`

## Server TTL

The SolvaPay server deduplicates idempotency keys within a TTL window. Keys presented after the TTL expires are treated as new requests. The `time_bucket="day"` default is conservative and safe for typical retry windows.
