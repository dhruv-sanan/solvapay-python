# Contract Tests

Smoke tests run against the SolvaPay sandbox API. Require `SOLVAPAY_SANDBOX_KEY` env var.

## Running locally

```bash
export SOLVAPAY_SANDBOX_KEY=sk_sandbox_...
uv run pytest tests/contract/ -m contract -v
```

## Cassette format

When `SOLVAPAY_RECORD=1` is set, `RecordingTransport` writes cassettes to `tests/contract/cassettes/`.
Without `SOLVAPAY_SANDBOX_KEY`, contract tests are skipped automatically.

### Schema

```json
[
  {
    "request": {
      "method": "POST",
      "url": "/v1/sdk/limits",
      "json": {"customerRef": "cus_123", "productRef": "prd_abc"}
    },
    "response": {
      "status_code": 200,
      "body": {"withinLimits": true, "remaining": 10, "meterName": "calls"},
      "headers": {}
    }
  }
]
```

## CI

Runs nightly via `.github/workflows/contract.yml` using `SOLVAPAY_SANDBOX_KEY` from GitHub Secrets.
