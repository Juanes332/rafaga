"""Size-checked upload reading."""

import io

import pytest
from fastapi import UploadFile

from app.core.errors.geometry_errors import UploadTooLargeError
from app.services.uploads.upload_service import read_limited


async def test_read_limited_returns_bytes_under_limit() -> None:
    """Small files pass through unchanged."""
    assert await read_limited(UploadFile(io.BytesIO(b"abc"), filename="a"), 1) == b"abc"


async def test_read_limited_rejects_streams_past_limit() -> None:
    """The byte count, not the header, decides."""
    big = UploadFile(io.BytesIO(b"0" * (1024 * 1024 + 1)), filename="a")
    with pytest.raises(UploadTooLargeError) as caught:
        await read_limited(big, 1)
    assert caught.value.details["limit_mb"] == 1


async def test_read_limited_rejects_declared_length_early() -> None:
    """A huge Content-Length is refused before reading."""
    with pytest.raises(UploadTooLargeError):
        await read_limited(UploadFile(io.BytesIO(b"x"), filename="a"), 1, 10**9)
