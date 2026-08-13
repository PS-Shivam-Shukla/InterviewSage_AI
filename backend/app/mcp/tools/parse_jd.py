"""
MCP Tool: parse_jd_text
Document Intelligence Layer — Phase 5 implementation.

Pre-processes raw job description text into a structured, section-annotated
payload ready for downstream LLM extraction by the JD Agent.
Requires: ftfy (listed in requirements.txt).
"""

from __future__ import annotations

import re
from typing import Any

import ftfy  # text normalization — pip install ftfy


_REQUIREMENTS_KW = [
    "requirements", "qualifications", "required", "must have",
    "you must", "mandatory", "essential",
]
_RESPONSIBILITIES_KW = [
    "responsibilities", "you will", "duties", "what you'll do",
    "day-to-day", "your role", "key duties",
]
_PREFERRED_KW = [
    "preferred", "nice to have", "bonus", "plus", "desired", "good to have",
]
_SKILLS_KW = [
    "skills", "technologies", "tech stack", "tools", "frameworks",
    "languages", "proficiency",
]


def parse_jd_text(raw_text: str) -> dict[str, Any]:
    """Normalize and pre-process raw job description text for agent consumption.

    Args:
        raw_text: Raw JD text pasted or extracted from an uploaded file.

    Returns:
        Dict with normalized_text, word_count, detected_sections, section
        presence flags, and extracted bullet_points.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Job description text is empty")

    normalized = _clean_jd(raw_text)
    lower = normalized.lower()

    has_req    = any(kw in lower for kw in _REQUIREMENTS_KW)
    has_resp   = any(kw in lower for kw in _RESPONSIBILITIES_KW)
    has_pref   = any(kw in lower for kw in _PREFERRED_KW)
    has_skills = any(kw in lower for kw in _SKILLS_KW)

    detected_sections = []
    if has_req:
        detected_sections.append("requirements")
    if has_resp:
        detected_sections.append("responsibilities")
    if has_pref:
        detected_sections.append("preferred")
    if has_skills:
        detected_sections.append("skills")

    return {
        "normalized_text": normalized,
        "word_count": len(normalized.split()),
        "detected_sections": detected_sections,
        "has_requirements_section": has_req,
        "has_responsibilities_section": has_resp,
        "has_preferred_section": has_pref,
        "has_skills_section": has_skills,
        "bullet_points": _extract_bullets(normalized),
    }


def _clean_jd(text: str) -> str:
    """Fix encoding, strip control chars, collapse blank lines."""
    text = ftfy.fix_text(text)
    text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return text.strip()


def _extract_bullets(text: str) -> list[str]:
    """Return bullet-point lines (symbol or numbered) from the text."""
    bullets = []
    for line in text.splitlines():
        stripped = line.strip()
        is_bullet = re.match(r"^[\-\•\*\·]\s+\S", stripped)
        is_numbered = re.match(r"^\d+\.\s+\S", stripped)
        if is_bullet or is_numbered:
            content = re.sub(r"^[\-\•\*\·\d\.]+\s+", "", stripped).strip()
            if len(content) > 5:
                bullets.append(content)
    return bullets
