# Troubleshooting

Common errors and how to fix them.

---

## 1. `AuthenticationError` — API key not set

**Symptom:**
```
solvapay.exceptions.AuthenticationError: No API key provided.
```

**Cause:** `SOLVAPAY_SECRET_KEY` env var is not set and no `api_key=` argument was passed.

**Fix:**
```bash
export SOLVAPAY_SECRET_KEY=sk_sandbox_...
```
Or pass it explicitly:
```python
sv = SolvaPay(api_key="sk_sandbox_...")
```

---

## 2. Async-in-sync deadlock

**Symptom:**
```
RuntimeError: cannot run event loop while another event loop is running
```
Or a call to `await sv.customers.ensure(...)` hangs indefinitely.

**Cause:** Mixing `AsyncSolvaPay` with sync framework code, or running async SDK methods from a Jupyter notebook without `await`.

**Fix:** Use `SolvaPay` (sync) for sync frameworks (FastAPI route handlers are async — use `AsyncSolvaPay` there). In Jupyter, `await` the call directly or use `asyncio.run()` in a standalone script.

```python
# FastAPI — use AsyncSolvaPay
@app.get("/check")
async def check(customer_ref: str):
    async with AsyncSolvaPay() as sv:
        result = await sv.limits.acheck(customer_ref=customer_ref, product_ref="prd_x")
    return result
```

---

## 3. `ModuleNotFoundError` — missing optional extra

**Symptom:**
```
ModuleNotFoundError: No module named 'fastmcp'
ModuleNotFoundError: No module named 'langchain_core'
ModuleNotFoundError: No module named 'tenacity'
```

**Cause:** Optional adapter or middleware not installed.

**Fix:** Install the relevant extra:
```bash
pip install solvapay-python[mcp]       # fastmcp
pip install solvapay-python[langchain] # langchain-core
pip install solvapay-python[retry]     # tenacity (RetryTransport)
pip install solvapay-python[fastapi]   # fastapi
pip install solvapay-python[bench]     # pytest-benchmark (dev only)
```

---

## 4. Contract tests skip silently

**Symptom:**
```
3 skipped — SOLVAPAY_SANDBOX_KEY not set
```

**Cause:** Sandbox tests require a live sandbox key and are intentionally skipped in CI unless the secret is configured.

**Fix:** For local sandbox testing:
```bash
export SOLVAPAY_SANDBOX_KEY=sk_sandbox_...
export SOLVAPAY_TEST_CUSTOMER_REF=cus_...
export SOLVAPAY_TEST_PRODUCT_REF=prd_...
uv run pytest -m contract
```

---

## 5. Windows virtualenv / `uv` path issues

**Symptom:**
```
FileNotFoundError: [WinError 2] The system cannot find the file specified
```
Or `uv run` fails to find the installed package.

**Cause:** Windows uses different path separators and virtualenv activation conventions.

**Fix:** Use `uv` from the project root — it manages the `.venv` automatically:
```bat
cd path\to\solvapay-python
uv sync --all-extras --dev
uv run pytest
```
Do not manually activate the venv; let `uv run` handle it.

---

## 6. `DeprecationWarning: Flat method deprecated` in test output

**Symptom:**
```
DeprecationWarning: Flat method deprecated. Use sv.customers.ensure(...) instead.
```

**Cause:** Old flat-method API (e.g. `sv.ensure_customer(...)`) is still being called. These shims emit a `DeprecationWarning` on every call and will be removed in v2.0.

**Fix:** Migrate to the namespace API:
```python
# Old (deprecated)
sv.ensure_customer("ext_ref")

# New (stable)
sv.customers.ensure("ext_ref")
```

To silence the warning in tests that still use the old path intentionally, add to `pyproject.toml`:
```toml
filterwarnings = ["ignore:Flat method deprecated:DeprecationWarning"]
```

---

## 7. `PaywallRequired` raised with `checkout_url=None`

**Symptom:**
```python
except PaywallRequired as e:
    print(e.checkout_url)  # None — no redirect URL available
```

**Cause:** In v0.8/v0.9, the SDK does NOT automatically call `checkout.create_session()` on every gate hit. Auto-minting is triggered only when the `LimitResponse` from the server includes a `checkoutUrl` field.

**Fix:** Use `paywall_state.gate()` for a fully enriched decision, or construct the checkout URL yourself:
```python
from solvapay.paywall_state import gate

decision = gate(sv, customer_ref=ref, product_ref="prd_x")
if decision.state != PaywallState.OK:
    redirect_to(decision.checkout_url)
```

Note: in v1.0 this behavior changes — see `HLD.md §V1.6 PW4`.

---

## 8. `verify_webhook` raises `ValueError`

**Symptom:**
```
ValueError: No valid signature found
ValueError: Request timestamp too old
```

**Cause:**
- Wrong secret (key rotation in progress, or `SOLVAPAY_WEBHOOK_SECRET` not matching the SolvaPay dashboard secret).
- System clock drift exceeding `tolerance` (default 300 seconds).

**Fix:**
```python
# Check your secret matches the SolvaPay dashboard exactly.
verify_webhook(body=raw_body, signature=header, secret=os.environ["SOLVAPAY_WEBHOOK_SECRET"])

# For testing with sign_webhook, pass a recent timestamp:
from solvapay.webhooks import sign_webhook
sig = sign_webhook(body, secret, timestamp=int(time.time()))
```

---

## 9. `mypy --strict` errors in paywall tests

**Symptom:**
```
error: Argument "client" to "Paywall" has incompatible type "MagicMock"; expected "SolvaPay"
```

**Cause:** `MagicMock(spec=SolvaPay)` does not know about instance attrs like `.limits`, `.customers` set in `__init__`. The spec reflects the class, not the instance.

**Fix:** Use plain `MagicMock()` without `spec=`:
```python
# WRONG
client = MagicMock(spec=SolvaPay)  # AttributeError on .limits

# CORRECT
client = MagicMock()
client.limits.check.return_value = LimitResponse(within_limits=True, remaining=5)
```

Add `# type: ignore[arg-type]` on the `Paywall(client=...)` line to satisfy mypy strict.

---

## 10. `pip install solvapay` vs `pip install solvapay-python`

**Symptom:**
```
ERROR: No matching distribution found for solvapay
```
Or: installed `solvapay` but `from solvapay import SolvaPay` is empty / old.

**Cause:** The distribution is named `solvapay-python` on PyPI (avoids namespace conflict before official adoption). The import name is still `solvapay`.

**Fix:**
```bash
pip install solvapay-python          # correct
pip install solvapay-python[mcp]     # with MCP adapter
```

The import surface is unchanged:
```python
from solvapay import SolvaPay, AsyncSolvaPay
```
