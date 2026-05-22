# RFC 0001 — SpendingPolicy + AgentIdentity + PolicyEnforcer

**Status:** Draft  
**Author:** Dhruv Sanan  
**Related issue:** [solvapay/solvapay-sdk#187](https://github.com/solvapay/solvapay-sdk/issues/187)

## Problem

In multi-agent pipelines, the same customer reference is shared across many tool calls.
Today there is no way for the SDK to enforce per-agent or per-session spending limits
without rolling custom middleware.

## Proposal

### `AgentIdentity`

```python
@dataclass(frozen=True)
class AgentIdentity:
    agent_id: str
    session_id: str | None = None
    model: str | None = None
    parent_agent_id: str | None = None
```

### `SpendingPolicy`

```python
@dataclass(frozen=True)
class SpendingPolicy:
    max_calls_per_session: int | None = None
    max_spend_usd: float | None = None
    allowed_products: frozenset[str] = field(default_factory=frozenset)
```

### `PolicyEnforcer` Protocol (already in `solvapay.paywall.policy`)

```python
class PolicyEnforcer(Protocol):
    def check(self, customer_ref: str, product: str, **context: Any) -> bool: ...
```

## Design notes

- `PolicyEnforcer` lives in `solvapay.experimental` until the shape stabilizes.
- `Paywall` accepts an optional `enforcer: PolicyEnforcer | None` kwarg. When set,
  the enforcer is called BEFORE the `check_limits` API call, enabling fast local
  rejection without a network round-trip.
- `AgentIdentity` is passed via `Context.extras["agent_identity"]` in `RequestSpec`.

## Open questions

1. Should `SpendingPolicy` be server-side (SolvaPay API) or client-side (SDK)?
2. How do we handle session TTL — SDK tracks it or SolvaPay backend?
3. `parent_agent_id` for hierarchical budgeting — necessary in v1?

## Next steps

Open GitHub Discussion linking this RFC for community input before implementation.
Ship `PolicyEnforcer` stub is already in `solvapay.paywall.policy` (v0.8).
