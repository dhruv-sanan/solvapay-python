# FastAPI Integration

## Webhook router

```python
from fastapi import FastAPI
from solvapay.fastapi import webhook_router

app = FastAPI()
app.include_router(
    webhook_router(
        secret="whsec_...",
        on_event=handle_event,
        path="/webhook",
    )
)
```

## ASGI webhook app (framework-agnostic)

```python
from fastapi import FastAPI
from solvapay.adapters.asgi import webhook_app
from solvapay.webhooks import WebhookPipeline

pipeline = WebhookPipeline(secrets=["whsec_..."])

async def handle(envelope):
    event = envelope.event
    print(f"Received {event['type']} for {event.get('customerId')}")

app = FastAPI()
app.mount("/webhook", webhook_app(pipeline, handle))
```

## Paywall decorator

```python
from fastapi import FastAPI, Request
from solvapay.paywall import require
from solvapay.exceptions import PaywallRequired

app = FastAPI()

@app.post("/api/search")
@require(product="prd_0QKI8NHF", plan="pln_pro", customer_ref_arg="customer_id")
async def search(customer_id: str, query: str):
    return {"results": [...]}

@app.exception_handler(PaywallRequired)
async def paywall_handler(req: Request, exc: PaywallRequired):
    return {"error": "upgrade_required", "checkout_url": exc.checkout_url}
```
