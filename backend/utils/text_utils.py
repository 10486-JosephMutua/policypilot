"""
PolicyPilot – Text Extraction Utilities
Handles PDF, DOCX, TXT, and Markdown extraction.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

from logger_config import app_log as log


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Extract plain text from a file given its bytes and filename."""
    ext = Path(filename).suffix.lower().lstrip(".")

    if ext == "pdf":
        return _extract_pdf(file_bytes)
    elif ext == "docx":
        return _extract_docx(file_bytes)
    elif ext in ("txt", "md"):
        return file_bytes.decode("utf-8", errors="replace")
    else:
        log.warning(f"Unknown extension '{ext}' – trying UTF-8 decode")
        return file_bytes.decode("utf-8", errors="replace")


def _extract_pdf(data: bytes) -> str:
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
        return "\n\n".join(text_parts)
    except Exception as e:
        log.exception("PDF extraction failed", exc_info=e)
        return ""


def _extract_docx(data: bytes) -> str:
    try:
        from docx import Document
        doc = Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        log.exception("DOCX extraction failed", exc_info=e)
        return ""
