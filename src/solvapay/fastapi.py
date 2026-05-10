"""Optional FastAPI integration. Requires `pip install solvapay[fastapi]`."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

try:
    from fastapi import APIRouter, HTTPException, Request
except ImportError as exc:
    raise ImportError(
        "FastAPI is not installed. Run: pip install solvapay[fastapi]"
    ) from exc

from solvapay.exceptions import SolvaPayError
from solvapay.webhooks import verify_webhook


def webhook_router(
    *,
    secret: str,
    on_event: Callable[[dict[str, Any]], Awaitable[None]],
    path: str = "/webhooks/solvapay",
) -> APIRouter:
    """Build an APIRouter that verifies and dispatches SolvaPay webhooks.

    Handles signature verification automatically. Mount it on your FastAPI app
    and implement your event logic in `on_event`.

    Args:
        secret: Webhook signing secret (starts with `whsec_`). Get from
                SOLVAPAY_WEBHOOK_SECRET env or your SolvaPay dashboard.
        on_event: Async callback that receives the verified event dict.
        path: URL path for the webhook endpoint. Default "/webhooks/solvapay".

    Returns:
        An APIRouter ready for `app.include_router(...)`.

    Example:
        import os
        from solvapay.fastapi import webhook_router

        async def handle_event(event: dict) -> None:
            if event["type"] == "purchase.created":
                ...  # grant access

        app.include_router(
            webhook_router(
                secret=os.environ["SOLVAPAY_WEBHOOK_SECRET"],
                on_event=handle_event,
            )
        )
    """
    router = APIRouter()

    @router.post(path)
    async def _solvapay_webhook(request: Request) -> dict[str, bool]:
        body = (await request.body()).decode()
        sig = request.headers.get("sv-signature", "")
        try:
            event = verify_webhook(body=body, signature=sig, secret=secret)
        except SolvaPayError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        await on_event(event)
        return {"received": True}

    return router
