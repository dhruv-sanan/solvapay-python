# Changelog

## 0.7.0 — 2026-05-17

Real-API alignment after testing against the SolvaPay sandbox revealed wire-format mismatches in three places. All existing public APIs continue to work; field aliases tolerate both old and new shapes.

### Fixed
- **`Customer.customer_ref`** now accepts `reference` (real API) in addition to `customerRef` via `validation_alias=AliasChoices(...)`. Existing callers using `customerRef` keep working.
- **`Customer.ensure_customer()`** (sync + async) reads `reference` from the API response; falls back to `customerRef` for backward compatibility. Raises if neither is present.
- **`BalanceResponse`** rewritten to mirror real API shape:
  - new fields: `credits: int`, `display_currency: str`, `credits_per_minor_unit: int`, `display_exchange_rate: float`
  - `balance: float` and `currency: str` are now computed properties for backward compatibility (`balance = credits / credits_per_minor_unit / 100`)
  - `plan` field removed (real API does not return it)

### Added
- **`solvapay.paywall_state.gate(client, *, customer_ref, product_ref, plan_ref=None)`** — one-call helper that runs `check_limits` + enriches the response with `create_checkout_session` (when checkout URL missing) and `get_customer` (when plan info missing) before classifying with `decide()`. Use this in product UX where you want one call to yield a fully actionable `GateDecision`.
- **`paywall.require` + `paywall.require_async`**: when blocked and the `LimitResponse` lacks a checkout URL, now automatically calls `create_checkout_session` and surfaces the resulting URL on `PaywallRequired.checkout_url`.
- **`examples/marketplace/`** — Streamlit marketplace demo of 4 paywalled AI agents (Google Gemini), running against real SolvaPay sandbox. Shows both integration styles: explicit `check_limits` + `decide()` and the `@paywall.require` decorator.

### Internal
- User-Agent bumped to `solvapay-python/0.7.0`
- 125 tests (up from 121), `mypy --strict` clean, `ruff` clean

## 0.6.0
- Admin endpoints (products, plans, merchant config)
- GitHub Actions trusted-publish to PyPI

## 0.5.0
- `paywall_state` pure-function state classifier (ACTIVATION_REQUIRED / TOPUP_REQUIRED / UPGRADE_REQUIRED)
- LangChain `monetize_tool` wrapper

## 0.4.0
- Full async client surface
- 5 lifecycle operations
- 13 typed webhook event classes with discriminated union parsing

## 0.3.0
- FastMCP example: AI agent with two paywalled tools

## 0.2.0
- `@paywall.require` decorator
- FastAPI webhook router

## 0.1.0
- Sync client, HMAC-SHA256 webhook verification, Pydantic v2 models, CI on 3 Python versions
