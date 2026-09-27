import io

import pytest
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.uploads import UploadError, public_url, save_upload

PNG_HEADER = b"\x89PNG\r\n\x1a\n" + b"0" * 20
JPEG_HEADER = b"\xff\xd8\xff" + b"0" * 20
WEBP_HEADER = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"0" * 20


def _upload_file(data: bytes, filename: str) -> UploadFile:
    return UploadFile(filename=filename, file=io.BytesIO(data))


async def test_png_bytes_named_jpg_are_stored_as_png(settings, app):
    session_factory = app.state.session_factory
    async with session_factory() as session:  # type: AsyncSession
        upload = await save_upload(_upload_file(PNG_HEADER, "photo.jpg"), "custom", 42, session, settings)
    assert upload.filename.endswith(".png")
    assert len(upload.filename) == len("0" * 32) + len(".png")


async def test_text_file_named_png_is_rejected_415(settings, app):
    session_factory = app.state.session_factory
    async with session_factory() as session:
        with pytest.raises(UploadError) as exc_info:
            await save_upload(_upload_file(b"not a real image", "photo.png"), "custom", 42, session, settings)
    assert exc_info.value.code == "unsupported_file_type"
    assert exc_info.value.http_status == 415


async def test_file_over_limit_is_rejected_413(settings, app):
    settings.max_upload_mb = 1
    oversized = JPEG_HEADER + b"0" * (1 * 1024 * 1024)
    session_factory = app.state.session_factory
    async with session_factory() as session:
        with pytest.raises(UploadError) as exc_info:
            await save_upload(_upload_file(oversized, "photo.jpg"), "custom", 42, session, settings)
    assert exc_info.value.code == "file_too_large"
    assert exc_info.value.http_status == 413


async def test_webp_is_detected_and_client_filename_is_ignored(settings, app):
    session_factory = app.state.session_factory
    async with session_factory() as session:
        upload = await save_upload(_upload_file(WEBP_HEADER, "evil/../name.exe"), "custom", 7, session, settings)
    assert upload.filename.endswith(".webp")
    assert "/" not in upload.filename
    assert upload.uploaded_by == 7


def test_public_url_prefixes_uploads_path():
    assert public_url("abc123.png") == "/uploads/abc123.png"
