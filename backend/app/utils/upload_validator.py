"""
Centralized Upload Validation Utility.
Implements file size enforcement, MIME type whitelisting, extension validation,
and filename sanitization to mitigate upload vulnerabilities (CWE-434, Path Traversal, Double Extensions).
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from fastapi import HTTPException, UploadFile, status
from app.core.config import settings

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
}

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}

# Dangerous filename patterns (path traversal, hidden files, dangerous double extensions)
PATH_TRAVERSAL_REGEX = re.compile(r"(\.\.[/\\]|[/\\]\.\.)")
DOUBLE_EXT_REGEX = re.compile(r"\.(pdf|docx|doc|txt)\.(exe|bat|sh|py|php|js|html|vbs|jar)$", re.IGNORECASE)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize uploaded filename to prevent Path Traversal and Directory Injection.
    """
    if not filename or not filename.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file upload: Filename cannot be empty.",
        )

    # Strip path directory components
    clean_name = os.path.basename(filename.strip())

    # Check path traversal attempts
    if PATH_TRAVERSAL_REGEX.search(filename) or ".." in filename or "/" in filename or "\\" in filename:
        # Check if basename stripped traversal attempts
        if PATH_TRAVERSAL_REGEX.search(filename) or ".." in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dangerous filename detected: Path traversal sequences ('..') are prohibited.",
            )

    # Check hidden files
    if clean_name.startswith(".") and not clean_name.startswith(".gitkeep"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dangerous filename detected: Uploading hidden files is prohibited.",
        )

    # Check dangerous double extension (e.g., resume.pdf.exe)
    if DOUBLE_EXT_REGEX.search(clean_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dangerous filename detected: Double executable extensions are prohibited.",
        )

    return clean_name


def validate_upload_file(file: UploadFile, content: bytes) -> str:
    """
    Validate file content, size, MIME type, and extension.
    Returns sanitized filename if valid.
    Raises HTTPException(400) if validation fails.
    """
    # 1. Empty file rejection
    if not content or len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file upload: File is empty (0 bytes).",
        )

    # 2. Maximum upload size enforcement
    if len(content) > settings.max_upload_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed limit of {settings.max_upload_size // (1024 * 1024)}MB.",
        )

    # 3. Filename sanitization
    filename = file.filename or "uploaded_file.pdf"
    clean_filename = sanitize_filename(filename)

    # 4. Extension validation
    ext = Path(clean_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions: {sorted(ALLOWED_EXTENSIONS)}.",
        )

    # 5. Content-Type (MIME type) validation
    content_type = (file.content_type or "").lower().split(";")[0].strip()
    if content_type and content_type not in ALLOWED_MIME_TYPES and content_type != "application/octet-stream":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported MIME type '{content_type}'. Allowed MIME types: {sorted(ALLOWED_MIME_TYPES)}.",
        )

    return clean_filename
