# Layer Architecture (HLD V1.1)

The SDK is organized into strict layers. Each layer may only import from layers below it.
Violations fail CI via `import-linter` (see `tools/importlinter.cfg`).

From **v0.9.3** the DAG is enforced as a single `type = layers` contract, replacing the
earlier three sparse `forbidden` contracts. `exhaustive = true` flags any new top-level
module that ships without an explicit layer assignment.

## Layer DAG

```
L7  solvapay.fastapi           — Top-level adapter shims (re-export from L6.adapters.*)
    solvapay.langchain
L6  solvapay.adapters          — Framework adapters (MCP, LangChain, ASGI, FastAPI)
L5  solvapay.paywall           — Paywall / AsyncPaywall primitives
    solvapay.webhooks          — Webhook verify + pipeline
L4  solvapay.client            — SolvaPay / AsyncSolvaPay public facades
    solvapay._async_client
L3  solvapay.operations        — Resource namespace operations (sv.customers.ensure etc.)
L2  solvapay.models            — Pydantic request/response models
L1  solvapay._http             — HTTP-client wrapper around the transport kernel
L0  solvapay._transport        — Transport Protocol + httpx impl + middleware
```

> **Note.** The HLD ships an aspirational L1 `_wire` slot that is currently unused.
> The shipped layout uses L1 for `_http` (the existing transport-kernel wrapper).
> When `_wire` ships, it will sit between `_transport` and `_http`.

## Allowed imports

A module at L_n may import from any module at L_(n-1) or below, plus the layer-independent
leaf modules (`exceptions`, `_stability`, `_config`, `idempotency`, `events`, `paywall_state`).

| Layer | May import |
|-------|------------|
| L0 `_transport` | stdlib, httpx, leaf modules |
| L1 `_http` | L0 + leaf modules |
| L2 `models` | stdlib, pydantic, leaf modules |
| L3 `operations` | L0–L2 + leaf modules |
| L4 `client` / `_async_client` | L0–L3 + leaf modules |
| L5 `paywall` / `webhooks` | L0–L4 + leaf modules |
| L6 `adapters` | L0–L5 + leaf modules |
| L7 `fastapi` / `langchain` (top-level shims) | L0–L6 + leaf modules |
| `tests/` | everything (permissive; tests live outside the `solvapay` container) |

Sibling modules on the same row (e.g. `paywall` ↔ `webhooks`, or `client` ↔ `_async_client`)
may not import each other. Each is independently constrained against the layers below.

## Why L7 = stability tier, not function (DG2 lock)

`solvapay.experimental` (reserved for v1.0) groups features by **stability**, not by
domain. A webhook adapter that is still unstable lives in L6 (adapters) while it's being
proven, then graduates to the canonical path once stable. This prevents the
`experimental` namespace from becoming a permanent home for half-finished features.

## Leaf modules (layer-independent)

These are listed in `exhaustive_ignores` in the contract because they have no upward edges
and no downward consumers beyond the boundary primitives:

- `solvapay.exceptions`
- `solvapay._stability`
- `solvapay._config`
- `solvapay.idempotency`
- `solvapay.events`
- `solvapay.paywall_state`

## TYPE_CHECKING imports

The contract sets `ignore_type_checking_imports = true`. Imports inside `if TYPE_CHECKING:`
blocks are stripped from the dependency graph, so cross-layer type hints (e.g.
`from solvapay.client import SolvaPay` for annotation purposes) do not trip the gate.
`mypy` still resolves these via the standard `from __future__ import annotations`
pattern enforced by `tools/lint_invariants.py`.

## Enforcement

```bash
~/.local/bin/uv run lint-imports --config tools/importlinter.cfg
```

Runs in CI on every push and PR. Also wrapped by `tests/test_layer_dag.py` so the
contract is exercised by `pytest` for local feedback.
