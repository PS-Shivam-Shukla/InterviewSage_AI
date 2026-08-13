"""
MCP Tool: compute_ats_score
Hybrid ATS alignment scorer:
  - Deterministic keyword-overlap computation in Python
  - Returns structured data that the ATS Agent's LLM call uses to
    generate phrasing suggestions
"""

import re
from typing import Dict, Any, List


def compute_ats_score(
    resume_skills: List[str],
    jd_required_skills: List[str],
    resume_text: str = "",
    jd_text: str = "",
) -> Dict[str, Any]:
    """
    Compute keyword / skill overlap between a resume and a JD.

    Args:
        resume_skills:      List of skills extracted from the resume.
        jd_required_skills: List of skills required by the JD.
        resume_text:        Full resume text for additional keyword mining.
        jd_text:            Full JD text for additional keyword mining.

    Returns:
        {
          "overlap_score": int (0-100),
          "matched_keywords": List[str],
          "missing_keywords": List[str],
          "resume_skill_count": int,
          "jd_skill_count": int,
        }
    """
    def normalise(skills: List[str]) -> set:
        return {s.lower().strip() for s in skills if s.strip()}

    resume_set = normalise(resume_skills)
    jd_set = normalise(jd_required_skills)

    # Also mine single-word tokens from the full texts if provided
    if resume_text:
        resume_set |= _extract_tech_tokens(resume_text)
    if jd_text:
        jd_set |= _extract_tech_tokens(jd_text)

    if not jd_set:
        return {
            "overlap_score": 0,
            "matched_keywords": [],
            "missing_keywords": [],
            "resume_skill_count": len(resume_set),
            "jd_skill_count": 0,
        }

    matched = sorted(resume_set & jd_set)
    missing = sorted(jd_set - resume_set)

    overlap_score = int(len(matched) / len(jd_set) * 100)

    return {
        "overlap_score": overlap_score,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "resume_skill_count": len(resume_set),
        "jd_skill_count": len(jd_set),
    }


def _extract_tech_tokens(text: str) -> set:
    """
    Extract likely technology/skill tokens from free text.
    Looks for capitalised acronyms (e.g. API, SQL, AWS)
    and common tech-word patterns.
    """
    tokens: set = set()
    # Acronyms: 2-6 uppercase letters
    for match in re.finditer(r"\b[A-Z]{2,6}\b", text):
        tokens.add(match.group(0).lower())
    # CamelCase identifiers (e.g. FastAPI, LangChain)
    for match in re.finditer(r"\b[A-Z][a-z]+[A-Z]\w*\b", text):
        tokens.add(match.group(0).lower())
    return tokens
