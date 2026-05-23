# Changelog

## 0.9.0 — 2026-05-23

Production polish + C1 adversarial-review closure. API-version pinning, idempotency TTL, webhook secret rotation, ASGI adapter, retry/recording transports, contract tests, lint automation, doc site, supply-chain hardening.

### Added
- **API-version pinning**: `SolvaPay(api_version="2026-05-22")` and `AsyncSolvaPay(api_version=...)` send `Solvapay-Version` header. Default pinned to `"2026-05-22"`. `api_version=None` omits the header. (HLD V1.13)
- **Idempotency time-bucket encoding**: `from_payload(*parts, time_bucket="day"|"hour"|None)`. Default `"day"` appends UTC date so keys roll at midnight, bounding replay ambiguity past server TTL. (HLD V1.14)
- **Webhook secret rotation**: `MultiSecretVerifier` full implementation — tries primary then secondary on signature mismatch; both comparisons constant-time. (HLD V1.7)
- **`AsyncInMemorySeenEventCache`**: async replay-dedup cache using `asyncio.Lock` for async webhook pipelines. (HLD V1.7)
- **`sign_webhook(body, secret, *, timestamp)`**: public helper to produce a valid `sv-signature` header for testing and outbound webhook fanout.
- **ASGI webhook adapter** (`solvapay[asgi]`): `webhook_app(pipeline, on_event, path)` returns a raw ASGI app mountable in Starlette, FastAPI, Litestar, or BlackSheep. (HLD V1.10)
- **`RetryTransport`**: middleware that retries `APIConnectionError`, `APITimeoutError`, `APIServerError`, `RateLimitError` — exponential backoff with jitter, max 3 attempts. Consults `OpSpec.retry_safety`; refuses to retry `NEVER` ops. (HLD V1.4, `solvapay[retry]`)
- **`RecordingTransport`**: records `(RequestSpec, ResponseSpec)` pairs to JSON cassettes; replays on subsequent runs. Enables offline contract tests. (HLD V1.4)
- **Sandbox contract tests** (`tests/contract/`): one test per op against real sandbox via `RecordingTransport`. Nightly CI workflow (`contract.yml`).
- **Lint invariants** (`tools/lint_invariants.py`): AST checks for 10 gotchas (future annotations, `hmac.compare_digest`, no `logging.basicConfig`, no `asyncio.run()`, alias discipline, etc.). Run in CI on every push.
- **Towncrier changelog automation**: `changelog.d/` fragments, PR gate requiring a fragment when `src/` changes, `towncrier>=23` dev dep.
- **MkDocs Material doc site**: `mkdocs.yml` + `docs/` skeleton (Quickstart, Reference, Architecture, Guides, Errors, Idempotency, Webhooks, Migration). Deploys to GitHub Pages on tag. (HLD V1.12)
- **Dependabot**: weekly Python + GitHub Actions dependency updates (`.github/dependabot.yml`).
- **`pip-audit` in CI**: dependency CVE scan on every push.
- **CI matrix expanded**: Ubuntu 3.10/3.11/3.12 + macOS 3.12 + Windows 3.12. (HLD V1.15)
- **`ResourceWarning` on unclosed `AsyncSolvaPay`**: `__del__` emits `ResourceWarning` if client is not closed and event loop is still running.
- **OpenAPI investigation RFC**: `docs/rfcs/0002-openapi-investigation.md`.

### Changed
- `pytest.ini_options.filterwarnings`: adds `ignore::DeprecationWarning:solvapay` so tests exercising deprecated flat-shim API do not fail on expected warnings.

---

## 0.8.0 — 2026-05-23

V1 architecture spine + AI-agent moat. 10 atomic commits establishing locked architecture invariants per HLD §V1.1–V1.19.

### Added
- **Transport Protocol kernel** (`solvapay._transport`): `Transport`/`AsyncTransport` Protocol shapes, `RequestSpec`/`ResponseSpec` frozen dataclasses, case-insensitive `Headers`, canonical middleware stack (`Redacting` → `Logging` → `IdempotencyHeader` → `ContextPropagating`), `default_stack()` recipe.
- **Operations registry + resource-namespace API**: `OpSpec` + `RetrySafety` enum, `REGISTRY`, path interpolation with `urllib.parse.quote`. All clients gain eager namespace attrs: `sv.customers`, `sv.checkout`, `sv.limits`, `sv.purchases`, `sv.usage`, `sv.products`, `sv.plans`, `sv.merchant`.
- **Paywall package** (`solvapay.paywall`): `Paywall`/`AsyncPaywall` split with type-narrowed construction, `PaywallRequired.checkout_mint_error`, `PayableToolMeta(_meta_version=1)`, `KwargsResolver`/`PositionalResolver`/`PydanticBodyResolver`, `@require`/`@require_async`/`@payable_tool` decorators.
- **Webhook pipeline** (`solvapay.webhooks`): `WebhookPipeline` with two-knob config (`max_clock_skew_seconds`, `replay_ttl_seconds`), atomic `SeenEventCache.try_claim` (`threading.Lock`), `MultiSecretVerifier` interface, `WebhookEnvelope` dataclass.
- **`solvapay.adapters.mcp`** (optional `solvapay[mcp]`): `@payable_tool` decorator + four schema flavors (`payable_tool_mcp_schema`, `payable_tool_openai_function`, `payable_tool_anthropic_tool`, `payable_tool_langchain_args_schema`), `register_payable_tool_fastmcp`.
- **Stability manifest** (`solvapay._stability`): `stable(X)→X` identity decorator registers in `MANIFEST`; `experimental` emits once-per-process `RuntimeWarning`; `deprecated(removed_in=)`. CI gate: `tools/api_diff.py` fails on `@stable` symbol removal without prior `@deprecated`.
- **Import-linter DAG gate**: `tools/importlinter.cfg` (3 contracts), `docs/architecture/layers.md`. CI fails on layer violation.
- **LangChain adapter refactor** (`solvapay.adapters.langchain`): Protocol duck-typing — no hard `langchain_core` import at module level; absorbs 0.3→0.4 churn.
- **Multi-framework demo** (`examples/multi-framework-paywall/`): one `@payable_tool`-decorated function runs across FastMCP, LangChain, and raw async — "one tool, three runtimes, one paywall."
- **Governance scaffold**: `CODEOWNERS`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `SUPPORT.md`, `CONTRIBUTING.md`, GitHub issue templates, PR template, `docs/rfcs/0001-spending-policy.md`.

### Changed
- **Flat methods deprecated**: `sv.ensure_customer()`, `sv.check_limits()`, etc. now emit `DeprecationWarning(stacklevel=2)` per call. Use `sv.customers.ensure()`, `sv.limits.check()`, etc. Flat shims removed in v2.0.
- **`langchain-core` upper bound**: `langchain-core>=0.3,<0.4` now enforced in both dev and optional deps.
- **`solvapay.langchain`** replaced by `solvapay.adapters.langchain`; old path is a deprecated shim.

### Deprecated
- `SolvaPayAPIError` — use `APIError`. Alias fires `DeprecationWarning`; removed in v2.0.
- All flat client methods (`sv.ensure_customer`, `sv.check_limits`, etc.) — use resource-namespace API.

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
