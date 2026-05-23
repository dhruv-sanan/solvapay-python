# Errors

```
SolvaPayError
├── APIError(status_code, body, request_id, error_code, error_message)
│   ├── AuthenticationError    # 401
│   ├── PermissionError        # 403
│   ├── NotFoundError          # 404
│   ├── RateLimitError(retry_after)   # 429
│   ├── InvalidRequestError    # other 4xx
│   └── APIServerError         # 5xx
├── APIConnectionError         # network failure
├── APITimeoutError            # timeout
└── PaywallRequired            # paywall gate hit
    .checkout_url: str | None
    .checkout_mint_error: APIError | None
```

## Handling errors

```python
from solvapay import SolvaPay
from solvapay.exceptions import (
    AuthenticationError,
    RateLimitError,
    APIConnectionError,
    PaywallRequired,
)

sv = SolvaPay()

try:
    sv.limits.check(customer_ref="cus_1", product_ref="prd_1")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited — retry after {e.retry_after}s")
except APIConnectionError:
    print("Network failure — safe to retry with idempotency key")
except PaywallRequired as e:
    print(f"Paywall hit. Checkout: {e.checkout_url}")
```

## `request_id`

Every `APIError` captures `request_id` from `x-request-id` or `x-correlation-id` response headers. Include this in support tickets.

## Legacy alias

`SolvaPayAPIError` is an alias for `APIError`. It emits `DeprecationWarning` and will be removed in v2.0. Use `APIError` directly.
