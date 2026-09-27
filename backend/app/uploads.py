"""Uploaded files on disk.

Owns magic-byte detection and naming; exposes `save_upload`, `public_url`, `UploadError`.
"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from .config import Settings
from .models import Upload

_SIGNATURES: list[tuple[bytes, str]] = [
    (b"\xff\xd8\xff", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
]


class UploadError(Exception):
    """Raised when an uploaded file fails validation. `code` is the machine error code."""

    def __init__(self, code: str, http_status: int) -> None:
        self.code = code
        self.http_status = http_status
        super().__init__(code)


def _detect_extension(data: bytes) -> str | None:
    for signature, ext in _SIGNATURES:
        if data.startswith(signature):
            return ext
    if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


async def save_upload(
    file: UploadFile, kind: str, user_id: int, session: AsyncSession, settings: Settings
) -> Upload:
    """Read the file in a bounded way, detect its type from content, store it under a
    server-generated name, and record a row in `uploads`.

    Raises UploadError("file_too_large", 413) if it exceeds settings.max_upload_mb,
    UploadError("unsupported_file_type", 415) if the content is not JPEG/PNG/WEBP.
    The client-supplied filename is never used for storage or type detection.
    """
    limit = settings.max_upload_mb * 1024 * 1024
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise UploadError("file_too_large", 413)

    ext = _detect_extension(data)
    if ext is None:
        raise UploadError("unsupported_file_type", 415)

    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    (upload_dir / filename).write_bytes(data)

    upload = Upload(filename=filename, kind=kind, uploaded_by=user_id, size=len(data))
    session.add(upload)
    await session.commit()
    await session.refresh(upload)
    return upload


def public_url(filename: str) -> str:
    """Map a stored filename to its public URL under the /uploads static mount."""
    return f"/uploads/{filename}"
