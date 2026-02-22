"""
PDF text extraction using PyMuPDF (fitz).
Returns (title, full_text).
"""

import io
from typing import Tuple

import fitz  # PyMuPDF


async def extract_pdf_text(file_bytes: bytes, filename: str = "document.pdf") -> Tuple[str, str]:
    """
    Extract all text from a PDF byte stream.
    Returns (title, full_text).
    """
    doc = fitz.open(stream=io.BytesIO(file_bytes), filetype="pdf")

    # Best-effort title from metadata
    meta = doc.metadata or {}
    title = meta.get("title") or filename.replace(".pdf", "").replace("_", " ").title()

    pages_text = []
    for page in doc:
        text = page.get_text("text")  # type: ignore[attr-defined]
        if text.strip():
            pages_text.append(text.strip())

    doc.close()
    full_text = "\n\n".join(pages_text)

    if not full_text.strip():
        raise ValueError("No extractable text found in the PDF. It may be a scanned image-only PDF.")

    return title, full_text
