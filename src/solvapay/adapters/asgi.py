"""ASGI webhook adapter — raw ASGI app from WebhookPipeline (HLD V1.7, V1.10).

Works as a mounted sub-app with Starlette, FastAPI, BlackSheep, Litestar, or
any ASGI server. No extra dependencies required (``solvapay[asgi]``).

Example (FastAPI)::

    from fastapi import FastAPI
    from solvapay.adapters.asgi import webhook_app
    from solvapay.webhooks import WebhookPipeline

    pipeline = WebhookPipeline(secrets=["whsec_..."])
    app = FastAPI()
    app.mount("/webhook", webhook_app(pipeline, on_event=handle_event))
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from solvapay.webhooks.pipeline import WebhookPipeline

# Standard ASGI type aliases
Scope = dict[str, Any]
Receive = Callable[[], Awaitable[dict[str, Any]]]
Send = Callable[[dict[str, Any]], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


def webhook_app(
    pipeline: WebhookPipeline,
    on_event: Callable[..., Awaitable[None] | None],
    *,
    path: str = "/webhook",
) -> ASGIApp:
    """Return a raw ASGI app that verifies + dispatches webhook events.

    Args:
        pipeline: Configured :class:`~solvapay.webhooks.WebhookPipeline`.
        on_event: Async or sync callable called with the
            :class:`~solvapay.webhooks.WebhookEnvelope` on success.
        path: URL path to respond on. Requests to other paths get 404.

    Returns:
        An ASGI 3-callable suitable for mounting or running directly.
    """

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await _not_found(send)
            return

        if scope.get("path") != path:
            await _not_found(send)
            return

        if scope.get("method", "GET").upper() != "POST":
            await _respond(send, 405, b"Method Not Allowed")
            return

        body = await _read_body(receive)
        sig = _get_header(scope, b"sv-signature")

        if sig is None:
            await _respond(send, 400, b"Missing sv-signature header")
            return

        try:
            envelope = pipeline.process(body=body, signature=sig)
        except Exception:
            await _respond(send, 400, b"Webhook verification failed")
            return

        result = on_event(envelope)
        if result is not None:
            await result

        await _respond(send, 200, b"ok")

    return app


async def _read_body(receive: Receive) -> bytes:
    body = b""
    while True:
        message = await receive()
        chunk = message.get("body", b"")
        body += chunk if isinstance(chunk, bytes) else chunk.encode()
        if not message.get("more_body", False):
            break
    return body


def _get_header(scope: Scope, name: bytes) -> str | None:
    for header_name, header_value in scope.get("headers", []):
        if header_name.lower() == name:
            value: str = header_value.decode("latin-1")
            return value
    return None


async def _respond(send: Send, status: int, body: bytes) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"text/plain"),
                (b"content-length", str(len(body)).encode()),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


async def _not_found(send: Send) -> None:
    await _respond(send, 404, b"Not Found")
