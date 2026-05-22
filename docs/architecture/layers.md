# Layer Architecture (HLD V1.1)

The SDK is organized into strict layers. Each layer may only import from layers below it.
Violations fail CI via `import-linter` (see `tools/importlinter.cfg`).

## Layer DAG

```
L0  solvapay._transport      — Transport Protocol + httpx impl + middleware
L1  solvapay._wire           — Wire codec (reserved; currently unused)
L2  solvapay.models          — Pydantic request/response models
L3  solvapay.operations      — Resource namespace operations (sv.customers.ensure etc.)
L4  solvapay.client          — SolvaPay / AsyncSolvaPay public facades
    solvapay._async_client
L5  solvapay.paywall         — Paywall / AsyncPaywall primitives
    solvapay.webhooks        — Webhook verify + pipeline
L6  solvapay.adapters        — Framework adapters (MCP, LangChain, ASGI)
L7  solvapay.experimental    — Experimental features (reserved)
L8  tests/                   — Test suite (permissive; may import L0–L7)
```

## Allowed imports

| Layer | May import |
|-------|-----------|
| L0 `_transport` | stdlib, httpx, `exceptions` |
| L1 `_wire` | L0 |
| L2 `models` | stdlib, pydantic |
| L3 `operations` | L0, L1, L2 |
| L4 `client` | L0–L3, `_config`, `exceptions` |
| L5 `paywall` | L0–L4 |
| L5 `webhooks` | L0–L2, `exceptions` |
| L6 `adapters` | L0–L5 |
| L7 `experimental` | L0–L6 |
| L8 `tests` | L0–L7 (no `from solvapay._*` outside `tests/internal/`) |

## Why L7 = stability tier, not function (DG2 lock)

`solvapay.experimental` groups features by **stability**, not by domain. A webhook adapter
that is still unstable lives in L6 (adapters) while it's being proven, then graduates to
the canonical path once stable. This prevents the "experimental" namespace from becoming a
permanent home for half-finished features.

## Enforcement

`uv run lint-imports --config tools/importlinter.cfg` — run in CI on every push.
