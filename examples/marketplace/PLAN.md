# Scope A — v0.7.0 SDK fixes + Marketplace Demo

## Goal
- Real SolvaPay sandbox compatibility (SDK shape bugs fixed)
- Demo shows OK + UPGRADE_REQUIRED with real checkout URL
- v0.7.0 shipped + 90s LinkedIn demo recorded

## Real-API findings (recorded 2026-05-16)

| Endpoint | SDK expects | Real API returns |
|---|---|---|
| `GET /v1/sdk/customers/{ref}` | `customerRef` | `reference` |
| `GET /v1/sdk/customers?externalRef=` | `customerRef` | `reference` |
| `POST /v1/sdk/customers` | `customerRef` | `reference` (assumed; mirrors GET) |
| `GET /v1/sdk/customers/{ref}/balance` | `{balance, currency, plan}` | `{customerRef, credits, displayCurrency, creditsPerMinorUnit, displayExchangeRate}` |
| `POST /v1/sdk/limits` | `{withinLimits, remaining, plan, creditBalance, checkoutUrl, ...}` | `{withinLimits, remaining, meterName}` (no plan, no checkout_url) |

## Workstreams

### A. SDK patches (me) — v0.7.0
1. **`models.py`**
   - `Customer`: alias `customerRef` → `reference` for `customer_ref` field (or rename field to `reference`)
   - `BalanceResponse`: drop `balance/currency/plan`; add `credits: int`, `display_currency: str` (alias `displayCurrency`), `credits_per_minor_unit: int` (alias `creditsPerMinorUnit`). Add `balance` property converting credits to display units for backwards-compat.
   - `LimitResponse`: keep optional fields tolerant; ensure missing `plan`, `creditBalance`, `checkoutUrl` parse to `None` (already partially the case — verify).
2. **`client.py` + `_async_client.py`**
   - `ensure_customer`: replace `existing.get("customerRef")` / `existing["customerRef"]` / `created["customerRef"]` with `reference` (lines 127, 128, 143 sync; 111, 112, 127 async)
3. **`paywall.py`**
   - When `within_limits == False` and `limits.checkout_url is None`, automatically call `create_checkout_session(customer_ref=..., product_ref=...)` and surface the resulting URL in both `PaywallRequired.checkout_url` and the raised banner. Mirror in async path.
4. **`paywall_state.py`**
   - Stays pure. `decide()` works on whatever `LimitResponse` it gets. New helper `decide_with_checkout(client, limits, *, customer_ref, product_ref)` for callers that want the checkout URL materialized.
5. **Tests**
   - Update `tests/conftest.py` fixtures to use real shape
   - Add regression test using captured real-API payloads
   - Verify `mypy --strict` + `ruff` pass
6. **Versioning**
   - Bump `pyproject.toml` to `0.7.0`
   - Update `__init__.py` __version__ if present
   - Update User-Agent in `_http.py` to `solvapay-python/0.7.0`
   - Append CHANGELOG entry

### B. Sandbox dashboard config (user) — parallel
1. On product `prd_0QKI8NHF`: add **Pro** pricing option (recurring, high reqs/month e.g. 10000) — NOT default
2. Subscribe Alice (`cus_CI5SGXJF`) to Pro
3. Leave Bob (`cus_YARKQDEN`) on Free (10 reqs/month default)
4. Pre-record: drain Bob's free reqs via the demo itself OR via direct API

### C. Marketplace demo wiring (me)
1. Use real `client.ensure_customer` for Bob (already created → idempotent)
2. `check_and_decide`: real `check_limits` → `decide()` → if blocked, mint real `create_checkout_session` URL
3. Real `track_usage` per call
4. Sidebar shows real `remaining` from `check_limits` + plan name from Customer purchases
5. 4 agents call real Google Gemini
6. "Show the SDK call" expander prints actual Python with real values
7. Reset button: re-bootstrap fresh blocked customer via `ensure_customer(timestamp-ref)` — for clean retakes

### D. video.md Snippet 4 (me)
- Write 90s script for marketplace walkthrough
- Update delivery checklist

## File list

**SDK:**
- `src/solvapay/models.py`
- `src/solvapay/client.py`
- `src/solvapay/_async_client.py`
- `src/solvapay/paywall.py`
- `src/solvapay/_http.py` (UA version bump)
- `pyproject.toml` (version 0.7.0)
- `tests/conftest.py` + impacted test files
- `CHANGELOG.md` (if present)

**Marketplace:**
- `examples/marketplace/app.py`
- `examples/marketplace/sdk_gateway.py`
- `examples/marketplace/agents.py`
- `examples/marketplace/demo_customers.py`
- `examples/marketplace/ui_components.py`
- `examples/marketplace/README.md`
- delete `examples/marketplace/_smoke.py` before commit

**Docs:**
- `/Users/dhruvsanan/Desktop/open-source/video.md` (Snippet 4)

## Execution sequence
1. ✅ Write PLAN.md + update video.md Snippet 4
2. Patch SDK models + client + async client
3. Patch paywall.py (auto-mint checkout URL on block)
4. Update tests + run pytest + mypy + ruff
5. Bump version + CHANGELOG
6. Rewire marketplace gateway/app/sidebar against patched SDK
7. Re-run `_smoke.py` against real sandbox — verify all paths produce expected typed states
8. Streamlit local end-to-end run
9. Once Alice on Pro: record 90s clip
10. Delete `_smoke.py`, commit, push, tag v0.7.0, publish on PyPI

## Open decisions
- Customer model field name: keep `customer_ref` with new alias OR rename to `reference`. **Decision: keep `customer_ref` with alias change** — preserves public API for existing users.
- `BalanceResponse.balance` semantics: `credits / credits_per_minor_unit` gives display-unit amount. Keep `balance: float` as computed property for backward compat. Real users see "$1000.00" not "100000 credits". 
- Plan info source: real `/limits` doesn't return plan; pull plan from `client.get_customer(ref).purchases[0].planSnapshot` if needed for sidebar.

## Risk register
| Risk | Mitigation |
|---|---|
| SolvaPay API returns different shape for `POST /customers` than GET | Test create explicitly during patches; tolerate both shapes |
| Pro plan subscribe flow not exposed in dashboard → can't subscribe Alice without API call | User flags blocker; I add `subscribe` helper or use checkout-session flow |
| `track_usage` fails for Bob (0 credits, Free plan) → can't drain him via API | Drain via UI (record Bob using 10 calls live = the demo itself) |
| `mypy --strict` fails after BalanceResponse rewrite | Add explicit type hints + computed property typing |
| Existing tests pass against old mock shape but break against real shape | Update fixtures to mirror real shape (captured in this PLAN.md table) |
