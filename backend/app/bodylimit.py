"""Body-size cap for the upload endpoints. Pure ASGI middleware — no new
packages. Owns the Content-Length pre-check and streamed byte counting;
exposes `BodySizeLimitMiddleware`.

Defense in depth for `POST /api/uploads` / `POST /api/admin/uploads`: without
this, an oversized multipart body is fully received and spooled to disk
before `save_upload`'s own MAX_UPLOAD_MB check ever runs. This rejects it
with 413 `file_too_large` up front (by Content-Length) or as soon as the
streamed body crosses the limit (when Content-Length is absent or lying),
before the app/python-multipart consumes any more of it.
"""
from __future__ import annotations

import json
from typing import Any, Awaitable, Callable, MutableMapping

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

_LIMITED_PATHS = {"/api/uploads", "/api/admin/uploads"}
_OVERHEAD_BYTES = 64 * 1024  # modest multipart-boundary/headers allowance on top of the file limit


class _BodyTooLarge(Exception):
    """Raised from inside the wrapped `receive` to unwind the downstream app
    before it processes any more of an oversized streamed body."""


class BodySizeLimitMiddleware:
    """Caps request bodies on the upload paths to `settings.max_upload_mb` (+ a
    small multipart overhead allowance). Every other path/method passes through
    untouched."""

    def __init__(self, app: ASGIApp, settings: Any) -> None:
        self.app = app
        self.limit = settings.max_upload_mb * 1024 * 1024 + _OVERHEAD_BYTES

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope.get("type") != "http"
            or scope.get("method") != "POST"
            or scope.get("path") not in _LIMITED_PATHS
        ):
            await self.app(scope, receive, send)
            return

        declared = _content_length(scope)
        if declared is not None and declared > self.limit:
            await _send_413(send)
            return

        seen = 0

        async def limited_receive() -> Message:
            nonlocal seen
            message = await receive()
            if message.get("type") == "http.request":
                seen += len(message.get("body") or b"")
                if seen > self.limit:
                    raise _BodyTooLarge()
            return message

        try:
            await self.app(scope, limited_receive, send)
        except _BodyTooLarge:
            await _send_413(send)


def _content_length(scope: Scope) -> int | None:
    for key, value in scope.get("headers") or []:
        if key == b"content-length":
            try:
                return int(value)
            except ValueError:
                return None
    return None


async def _send_413(send: Send) -> None:
    body = json.dumps({"detail": "file_too_large"}).encode()
    await send(
        {
            "type": "http.response.start",
            "status": 413,
            "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())],
        }
    )
    await send({"type": "http.response.body", "body": body})
