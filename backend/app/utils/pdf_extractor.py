"""
PDF and Document Text Extraction Utility.
Uses PyMuPDF (fitz) with PyPDF2 fallbacks and NUL byte sanitization.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    """
    Extract readable text from PDF binary bytes.
    Sanitizes NUL (0x00) characters to prevent DB insertion failures.
    """
    if not file_bytes:
        return ""

    extracted_text = ""

    # Strategy 1: PyMuPDF (fitz)
    try:
        import fitz
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text_parts = []
        for page in doc:
            page_text = page.get_text()
            if page_text:
                text_parts.append(page_text)
        doc.close()
        extracted_text = "\n".join(text_parts)
    except Exception as e1:
        logger.warning(f"PyMuPDF extraction failed: {e1}. Trying PyPDF2 fallback...")
        # Strategy 2: PyPDF2 fallback
        try:
            import io

            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            text_parts = []
            for page in reader.pages:
                txt = page.extract_text()
                if txt:
                    text_parts.append(txt)
            extracted_text = "\n".join(text_parts)
        except Exception as e2:
            logger.warning(f"PyPDF2 extraction failed: {e2}. Falling back to utf-8 decode.")
            try:
                extracted_text = file_bytes.decode("utf-8", errors="ignore")
            except Exception:
                extracted_text = ""

    # CRITICAL: Sanitize NUL (0x00) bytes to prevent PostgreSQL/SQLite DB crashes
    clean_text = extracted_text.replace("\x00", "").strip()
    return clean_text
