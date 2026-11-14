"""Rasterize background pages to PNG within a pixel budget."""

import io
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, UnidentifiedImageError

MAX_SIDE_PX = 4096
SIGNATURES = {".png": b"\x89PNG\r\n\x1a\n", ".jpg": b"\xff\xd8\xff", ".jpeg": b"\xff\xd8\xff",
              ".pdf": b"%PDF"}


def matches_signature(extension: str, data: bytes) -> bool:
    """Return whether the bytes start with the extension's magic number."""
    return data.startswith(SIGNATURES.get(extension, b"\0\0\0\0\0"))


def count_pages(extension: str, data: bytes) -> int:
    """Return the page count; raises ValueError for unreadable files."""
    if extension == ".pdf":
        try:
            return len(pdfium.PdfDocument(data))
        except pdfium.PdfiumError as exc:
            raise ValueError("unreadable pdf") from exc
    try:
        Image.open(io.BytesIO(data)).verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("unreadable image") from exc
    return 1


def _png(image: Image.Image) -> bytes:
    """Encode an image as PNG, shrunk to the pixel budget."""
    image.thumbnail((MAX_SIDE_PX, MAX_SIDE_PX))
    buffer = io.BytesIO()
    image.convert("RGBA" if image.mode in ("RGBA", "LA", "P") else "RGB").save(buffer, "PNG")
    return buffer.getvalue()


def render_page(path: Path, page: int) -> bytes:
    """Return the 1-based page of the stored file as PNG bytes."""
    if path.suffix.lower() == ".pdf":
        doc = pdfium.PdfDocument(str(path))
        pdf_page = doc[page - 1]
        width, height = pdf_page.get_size()
        scale = min(3.0, MAX_SIDE_PX / max(width, height))
        return _png(pdf_page.render(scale=scale).to_pil())
    return _png(Image.open(path))
