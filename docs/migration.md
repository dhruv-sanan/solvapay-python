# Migration Guide

## v0.7.x → v0.8.x

### Flat methods are now deprecated

All flat methods on `SolvaPay` / `AsyncSolvaPay` (e.g. `sv.ensure_customer()`) now emit `DeprecationWarning` and will be **removed in v2.0**.

Migrate to the resource namespace API:

| Old (v0.7) | New (v0.8+) |
|---|---|
| `sv.ensure_customer(ref)` | `sv.customers.ensure(ref)` |
| `sv.get_customer(ref)` | `sv.customers.get(ref)` |
| `sv.check_limits(...)` | `sv.limits.check(...)` |
| `sv.create_checkout_session(...)` | `sv.checkout.create_session(...)` |
| `sv.track_usage(...)` | `sv.usage.track(...)` |
| `sv.cancel_purchase(ref)` | `sv.purchases.cancel(ref)` |
| `sv.reactivate_purchase(ref)` | `sv.purchases.reactivate(ref)` |

Async variants: prepend `a` to the method name, e.g. `sv.customers.aensure(ref)`.

### Mock pattern changed

```python
# Old (v0.7) — WRONG for v0.8
client = MagicMock(spec=SolvaPay)
client.check_limits.return_value = ...

# New (v0.8+) — CORRECT
client = MagicMock()
client.limits.check.return_value = ...
```

### `webhooks.py` and `paywall.py` are now packages

Imports from `solvapay.webhooks` and `solvapay.paywall` still work — the packages re-export everything at the same names.

## v0.6.x → v0.7.x

### Wire format fixes

- `Customer.customer_ref` now accepts `reference` (real API) and `customerRef` (legacy) via `AliasChoices`
- `BalanceResponse.balance` is now major-unit (dollars), not cents
- Use `paywall_state.gate()` instead of manual enrichment after `check_limits`

## SolvaPayAPIError alias

`SolvaPayAPIError = APIError` is a deprecated alias. Use `APIError` directly. Will be removed in v2.0.
