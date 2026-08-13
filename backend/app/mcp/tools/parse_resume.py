"""
MCP Tool: parse_resume_pdf
Document Intelligence Layer — Phase 5 implementation.

Architecture contract:
  - No AI Agent reads raw PDF files directly.
  - This is the ONLY component that processes raw uploaded documents.
  - Requires: pymupdf, python-docx, ftfy (all listed in requirements.txt).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import fitz   # PyMuPDF  — pip install pymupdf
import docx   # python-docx — pip install python-docx
import ftfy   # text normalization — pip install ftfy


def parse_resume_pdf(file_path: str) -> dict[str, Any]:
    """Extract raw text from a resume file (PDF, DOCX, or TXT).

    Args:
        file_path: Absolute path to the resume file.

    Returns:
        Dict with keys: raw_text, file_type, page_count, char_count, needs_ocr.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _parse_pdf(path)
    if suffix in (".docx", ".doc"):
        return _parse_docx(path)
    if suffix == ".txt":
        cleaned = _clean_text(path.read_text(encoding="utf-8", errors="replace"))
        return {
            "raw_text": cleaned,
            "file_type": "txt",
            "page_count": 1,
            "char_count": len(cleaned),
            "needs_ocr": False,
        }
    raise ValueError(
        f"Unsupported file type: {suffix!r}. Supported: .pdf, .docx, .txt"
    )


def _parse_pdf(path: Path) -> dict[str, Any]:
    """Extract text from a PDF file using PyMuPDF."""
    doc = fitz.open(str(path))
    pages = [page.get_text("text") for page in doc]
    doc.close()
    cleaned = _clean_text("\n".join(pages))
    return {
        "raw_text": cleaned,
        "file_type": "pdf",
        "page_count": len(pages),
        "char_count": len(cleaned),
        "needs_ocr": len(cleaned.strip()) < 50,
    }


def _parse_docx(path: Path) -> dict[str, Any]:
    """Extract text from a DOCX file using python-docx."""
    document = docx.Document(str(path))
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    cleaned = _clean_text("\n".join(paragraphs))
    return {
        "raw_text": cleaned,
        "file_type": "docx",
        "page_count": 1,
        "char_count": len(cleaned),
        "needs_ocr": False,
    }


def _clean_text(text: str) -> str:
    """Fix encoding, strip control chars, and collapse blank lines."""
    text = ftfy.fix_text(text)
    text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return text.strip()
