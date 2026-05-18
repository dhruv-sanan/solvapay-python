# Changelog

## 0.7.2 — 2026-05-18

Bug fixes and documentation update.

### Fixed
- **`paywall.require_async`**: `AsyncSolvaPay()` instantiated without a caller-supplied `client=` was not closed after the decorated function returned, leaking the underlying `httpx.AsyncClient` connection pool. Wrapped in `try/finally`; `await sv.aclose()` called when the decorator owns the client.
- **`examples/fastmcp-paywall/pyproject.toml`**: dependency used wrong PyPI dist name (`solvapay`) and a stale `@v0.3.0` pin. Updated to `solvapay-python>=0.7.2`.
- **`examples/langchain-paywall/pyproject.toml`**: same wrong dist name and stale `@v0.5.0` pin. Updated to `solvapay-python[langchain]>=0.7.2`.

### Docs
- **README** updated to v0.7.1 surface: `paywall_state.gate()`, error hierarchy, idempotency keys, admin ops table, marketplace example, roadmap entries for v0.7.0 and v0.7.1.

### Internal
- `tests/test_lifecycle.py` reformatted (ruff format compliance)

## 0.7.1 — 2026-05-17

Payments-grade hardening: structured errors, idempotency keys, py.typed, structured logging.

### Added
- **Structured error hierarchy** (`exceptions.py`): `APIError` base with `status_code`, `request_id`, `error_code`, `error_message`. Subclasses: `AuthenticationError` (401), `PermissionError` (403), `NotFoundError` (404), `RateLimitError` (429, adds `.retry_after`), `InvalidRequestError` (4xx), `APIServerError` (5xx), `APIConnectionError`, `APITimeoutError`. `SolvaPayAPIError` aliased to `APIError` for back-compat.
- **Idempotency keys** on all mutating ops: `create_checkout_session`, `ensure_customer`, `track_usage`, `cancel_purchase`, `reactivate_purchase`, `create_product`, `clone_product`, `create_plan` all accept `idempotency_key: str | None = None`. Header casing: `Idempotency-Key` (matches TS SDK).
- **`solvapay.idempotency.from_payload(*parts)`** — SHA256 of stable-serialized payload parts → 32-hex-char deterministic key.
- **PEP 561 `py.typed` marker** — downstream mypy users no longer see `Any` on `solvapay.*` imports.
- **Structured logging** at `solvapay.http` logger: INFO on success (method, path, status, request_id, duration_ms), WARNING on 4xx/5xx (adds body_excerpt ≤200 chars). Never calls `logging.basicConfig`. Optional `logger=` injection on `SolvaPay`/`AsyncSolvaPay` constructors for `loguru`/`structlog`.
- **Secret redaction**: `Authorization` header never appears in logs. Verified by `tests/test_redaction.py`.
- **pyproject classifiers**: `Development Status :: 4 - Beta`, `Framework :: AsyncIO`, `Topic :: Office/Business :: Financial`, `Typing :: Typed`.

### Internal
- User-Agent bumped to `solvapay-python/0.7.1`
- 142 tests (up from 125), `mypy --strict` clean, `ruff` clean

## 0.7.0 — 2026-05-17

Real-API alignment after testing against the SolvaPay sandbox revealed wire-format mismatches.

### Fixed
- **`Customer.customer_ref`** now accepts `reference` (real API) in addition to `customerRef` via `validation_alias=AliasChoices(...)`.
- **`ensure_customer()`** reads `reference` from API response; falls back to `customerRef`. Raises if neither present.
- **`BalanceResponse`** rewritten: `credits`, `display_currency`, `credits_per_minor_unit`, `display_exchange_rate`; `balance` and `currency` kept as computed properties.

### Added
- **`paywall_state.gate()`** — one-call enrichment helper (limits + checkout URL + plan via `get_customer`).
- **`paywall.require` / `require_async`**: auto-mints checkout URL when `LimitResponse.checkout_url is None`.
- **`examples/marketplace/`** — Streamlit demo with 4 paywalled AI agents (Google Gemini) against real SolvaPay sandbox.

### Internal
- User-Agent `solvapay-python/0.7.0`. 125 tests (up from 121). `mypy --strict` clean.

## 0.6.0
- Admin endpoints (products, plans, merchant config). GitHub Actions trusted-publish to PyPI.

## 0.5.0
- `paywall_state` classifier (ACTIVATION_REQUIRED / TOPUP_REQUIRED / UPGRADE_REQUIRED). LangChain `monetize_tool`.

## 0.4.0
- Full async client. 5 lifecycle operations. 13 typed webhook event classes.

## 0.3.0
- FastMCP example: AI agent with two paywalled tools.

## 0.2.0
- `@paywall.require` decorator. FastAPI webhook router.

## 0.1.0
- Sync client, HMAC-SHA256 webhook verification, Pydantic v2 models, CI on 3 Python versions.
