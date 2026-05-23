# Webhooks

## Verify a webhook

```python
from solvapay.webhooks import verify_webhook

event = verify_webhook(
    body=request.body,      # raw request body string
    signature=request.headers["sv-signature"],
    secret="whsec_...",
    tolerance=300,          # max clock skew in seconds
)
print(event["type"])  # e.g. "payment.succeeded"
```

## WebhookPipeline (verify + dedup)

```python
from solvapay.webhooks import WebhookPipeline

pipeline = WebhookPipeline(
    secrets=["whsec_primary", "whsec_rotating"],
    max_clock_skew_seconds=300,   # two separate knobs
    replay_ttl_seconds=600,
)

envelope = pipeline.process(body=raw_bytes, signature=sig_header)
print(envelope.event_id)
print(envelope.event["type"])
```

## Secret rotation

Pass multiple secrets — primary first, fallback after:

```python
pipeline = WebhookPipeline(secrets=["whsec_new", "whsec_old"])
```

The pipeline tries the primary HMAC; on mismatch (not age failure), tries the secondary.

## Replay protection

`InMemorySeenEventCache` deduplicates by `event_id` for `replay_ttl_seconds`. Replace with a Redis-backed cache for multi-process deployments:

```python
from solvapay.webhooks import WebhookPipeline, SeenEventCache

class RedisCache:
    def try_claim(self, event_id: str, ttl_seconds: int) -> bool:
        return redis.set(f"webhook:{event_id}", 1, ex=ttl_seconds, nx=True)

pipeline = WebhookPipeline(secrets=["whsec_..."], seen_cache=RedisCache())
```

## ASGI adapter

```python
from solvapay.adapters.asgi import webhook_app
from solvapay.webhooks import WebhookPipeline

pipeline = WebhookPipeline(secrets=["whsec_..."])

async def handle(envelope):
    print(envelope.event["type"])

app = webhook_app(pipeline, handle, path="/webhook")
# Mount on FastAPI: app.mount("/webhook", asgi_app)
```

## Signing webhooks (for tests)

```python
from solvapay.webhooks import sign_webhook

sig = sign_webhook(b'{"id":"evt_1"}', secret="whsec_test")
# → "t=1234567890,v1=abc123..."
```
