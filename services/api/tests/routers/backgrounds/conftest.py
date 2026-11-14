"""Builders for background plan files."""

import io

import pypdfium2 as pdfium
from PIL import Image


def png_bytes(size: tuple[int, int] = (200, 100)) -> bytes:
    """Return a PNG of the given pixel size."""
    buffer = io.BytesIO()
    Image.new("RGB", size, (200, 30, 30)).save(buffer, "PNG")
    return buffer.getvalue()


def pdf_bytes(pages: int = 2) -> bytes:
    """Return a PDF with blank pages of different sizes."""
    doc = pdfium.PdfDocument.new()
    for i in range(pages):
        doc.new_page(300 + 100 * i, 200)
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
