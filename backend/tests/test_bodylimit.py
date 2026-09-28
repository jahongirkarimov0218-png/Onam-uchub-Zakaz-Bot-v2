"""Unit tests for app.bodylimit at the raw ASGI seam: a fake downstream app
records what it receives, so we can prove the body was never fully read/relayed
past the limit — httpx can't reliably fake a lying Content-Length header."""
from app.bodylimit import BodySizeLimitMiddleware

LIMIT_MB = 1
LIMIT_BYTES = LIMIT_MB * 1024 * 1024 + 64 * 1024  # matches the middleware's own overhead allowance


class _Settings:
    max_upload_mb = LIMIT_MB


def _scope(path: str = "/api/uploads", method: str = "POST", content_length: int | None = None):
    headers = []
    if content_length is not None:
        headers.append((b"content-length", str(content_length).encode()))
    return {"type": "http", "method": method, "path": path, "headers": headers}


class _RecordingApp:
    """Fake downstream ASGI app: pulls http.request messages via `receive` until
    told to stop, recording total bytes it was handed; never sends a response
    on its own so tests can tell the middleware's own 413 apart from the app's."""

    def __init__(self, chunks: int = 100):
        self.received_bytes = 0
        self.chunks_pulled = 0
        self.max_chunks = chunks

    async def __call__(self, scope, receive, send):
        for _ in range(self.max_chunks):
            message = await receive()
            self.chunks_pulled += 1
            self.received_bytes += len(message.get("body") or b"")
            if not message.get("more_body"):
                break


def _collector():
    sent = []

    async def send(message):
        sent.append(message)

    return sent, send


async def test_content_length_above_limit_is_rejected_before_receive_is_called():
    async def receive():
        raise AssertionError("body must not be read when Content-Length already exceeds the limit")

    sent, send = _collector()
    inner = _RecordingApp()
    mw = BodySizeLimitMiddleware(inner, _Settings())

    await mw(_scope(content_length=LIMIT_BYTES + 1), receive, send)

    assert sent[0]["type"] == "http.response.start"
    assert sent[0]["status"] == 413
    assert inner.received_bytes == 0


async def test_content_length_within_limit_is_forwarded_to_the_app():
    body = b"x" * 1000

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    sent, send = _collector()
    inner = _RecordingApp()
    mw = BodySizeLimitMiddleware(inner, _Settings())

    await mw(_scope(content_length=len(body)), receive, send)

    assert inner.received_bytes == len(body)
    assert sent == []  # the middleware itself sent nothing; the fake app is silent too


async def test_streamed_body_without_content_length_exceeding_limit_is_rejected_and_not_spooled_past_it():
    chunk = b"y" * (64 * 1024)  # 64 KiB per chunk
    total_chunks = (LIMIT_BYTES // len(chunk)) + 5  # enough to cross the limit if unchecked
    calls = {"n": 0}

    async def receive():
        calls["n"] += 1
        return {"type": "http.request", "body": chunk, "more_body": True}

    sent, send = _collector()
    inner = _RecordingApp(chunks=total_chunks)
    mw = BodySizeLimitMiddleware(inner, _Settings())

    await mw(_scope(content_length=None), receive, send)

    assert sent[0]["type"] == "http.response.start"
    assert sent[0]["status"] == 413
    # not spooled past the limit: the app was handed at most one chunk beyond
    # the threshold, never anywhere near all `total_chunks` worth of bytes.
    assert inner.received_bytes <= LIMIT_BYTES + len(chunk)
    assert calls["n"] < total_chunks


async def test_non_upload_path_is_never_inspected():
    async def receive():
        return {"type": "http.request", "body": b"irrelevant", "more_body": False}

    sent, send = _collector()
    inner = _RecordingApp()
    mw = BodySizeLimitMiddleware(inner, _Settings())

    await mw(_scope(path="/health", method="GET", content_length=LIMIT_BYTES + 1), receive, send)

    assert inner.received_bytes == len(b"irrelevant")
    assert sent == []


async def test_413_response_body_reports_file_too_large():
    async def receive():
        raise AssertionError("unused")

    sent, send = _collector()
    mw = BodySizeLimitMiddleware(_RecordingApp(), _Settings())

    await mw(_scope(content_length=LIMIT_BYTES + 1), receive, send)

    body_message = sent[1]
    assert body_message["type"] == "http.response.body"
    assert b"file_too_large" in body_message["body"]
