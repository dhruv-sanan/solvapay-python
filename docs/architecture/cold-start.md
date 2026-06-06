# Cold-Start Performance

## What we measure

`python -X importtime -c "import solvapay"` prints a line per imported module:

```
import time:    <self_µs> | <cumulative_µs> | <module_name>
```

The `cumulative_µs` column for the root `solvapay` module is the total cold-import cost — the number we track.

## The baseline harness (`tests/test_cold_import.py`)

Introduced in v0.9.2, `tests/test_cold_import.py` runs the above command via `subprocess` and:

1. **First run** — writes `tests/_baselines/cold_import.json` with the measured value.
2. **Subsequent runs** — asserts the current measurement is within **1.5×** of the baseline.

The 1.5× regression factor is intentionally loose — it catches gross regressions (importing a new heavy dependency eagerly) without failing on normal M-series vs CI machine variance.

The committed baseline is re-measured and updated whenever a structural change affects import cost (e.g. lazy adapter imports in v0.9.2).

### Current baseline

| Version | M-series (macOS) | What changed |
|---------|-----------------|--------------|
| v0.9.1  | ~88 ms          | Initial measurement |
| v0.9.2  | ~100 ms         | PEP 562 `__getattr__` + `__dir__` added; adapters lazy |

## PEP 562 lazy adapter imports

Adapter modules (`solvapay.adapters.mcp`, `solvapay.adapters.langchain`, etc.) depend on optional heavy packages — `fastmcp`, `langchain-core`, `fastapi`. These are only installed when the user runs `pip install solvapay-python[mcp]` etc.

Before v0.9.2, accessing `solvapay.adapters` required an explicit subpackage import. In v0.9.2, `solvapay/__init__.py` defines a PEP 562 `__getattr__` that loads `solvapay.adapters` lazily on first attribute access:

```python
# In solvapay/__init__.py
_LAZY_MODULES = {"adapters": "solvapay.adapters"}

def __getattr__(name: str) -> object:
    if name in _LAZY_MODULES:
        import importlib
        mod = importlib.import_module(_LAZY_MODULES[name])
        globals()[name] = mod  # cache for subsequent accesses
        return mod
    raise AttributeError(f"module 'solvapay' has no attribute {name!r}")

def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_LAZY_MODULES))
```

This ensures:
- `import solvapay` — **zero adapter cost** regardless of which extras are installed.
- `solvapay.adapters` — triggers a single load on first access, cached thereafter.
- `from solvapay.adapters import mcp` — works via Python's normal subpackage import path (unaffected by `__getattr__`).
- `dir(solvapay)` — lists `"adapters"` per PEP 562 convention.

## v1.0 hard budget (HLD §V1.20)

v0.9.2 ships **measurement only**. The hard gate is a v1.0 feature:

| Environment | Budget |
|-------------|--------|
| M-series Mac | < 150 ms |
| x86 CI | < 300 ms |

v1.0 achieves this primarily via **`@cached_property` lazy namespace materialization** — `SolvaPay.__init__` will no longer eagerly construct `customers`, `checkout`, `limits`, etc. Each namespace is constructed on first access (`sv.customers.ensure(...)`) and cached as an instance attribute. This eliminates the linear startup cost as V2/V3 expand the namespace count.

See `HLD.md §V1.3 RN1-v2` and `§V1.20` for the full contract.
