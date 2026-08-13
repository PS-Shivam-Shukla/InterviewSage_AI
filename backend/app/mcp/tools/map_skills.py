"""
MCP Tool: map_skills
Skill Intelligence MCP — Phase 5 implementation.

Computes resume vs job description skill alignment:
  - Matched skills (candidate has them)
  - Missing skills (JD requires them, candidate lacks them)
  - ATS overlap score (0-100)
  - Strengths and weaknesses
  - Interview focus areas

This is pure deterministic computation — no LLM call here.
The LLM is used upstream to *extract* the skill lists; this tool
computes the comparison deterministically.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Set


def map_skills(
    resume_skills: List[str],
    jd_required_skills: List[str],
    jd_preferred_skills: List[str] | None = None,
    resume_text: str = "",
    jd_text: str = "",
) -> Dict[str, Any]:
    """
    Compare candidate resume skills against job description requirements.

    Args:
        resume_skills: List of skills extracted from the resume.
        jd_required_skills: Mandatory skills from the job description.
        jd_preferred_skills: Optional preferred/nice-to-have skills.
        resume_text: Full resume text for keyword coverage fallback.
        jd_text: Full JD text for keyword coverage fallback.

    Returns:
        {
          "matched_skills": list[str],
          "missing_skills": list[str],
          "preferred_matched": list[str],
          "ats_overlap_score": int,         # 0-100
          "keyword_coverage_score": int,    # 0-100, text-level match
          "strengths": list[str],
          "weaknesses": list[str],
          "interview_focus_areas": list[str],
          "confidence": float,
        }
    """
    jd_preferred = jd_preferred_skills or []

    # Normalize all skill lists for comparison
    normalized_resume = {_normalize(s) for s in resume_skills}
    normalized_required = {_normalize(s) for s in jd_required_skills}
    normalized_preferred = {_normalize(s) for s in jd_preferred}

    # ── Mandatory skill match ─────────────────────────────────
    matched_norm: Set[str] = set()
    missing_norm: Set[str] = set()

    for skill_norm in normalized_required:
        # Check exact match first, then substring containment
        if skill_norm in normalized_resume or _fuzzy_match(skill_norm, normalized_resume):
            matched_norm.add(skill_norm)
        else:
            # Also check raw resume text for abbreviations / compound terms
            skill_raw = skill_norm.replace("_", " ")
            if resume_text and skill_raw in resume_text.lower():
                matched_norm.add(skill_norm)
            else:
                missing_norm.add(skill_norm)

    # ── Preferred skill match ─────────────────────────────────
    preferred_matched_norm: Set[str] = set()
    for skill_norm in normalized_preferred:
        if skill_norm in normalized_resume or _fuzzy_match(skill_norm, normalized_resume):
            preferred_matched_norm.add(skill_norm)

    # ── ATS score — ratio of mandatory skills matched ─────────
    total_required = len(normalized_required)
    ats_score = (
        int(len(matched_norm) / total_required * 100) if total_required > 0 else 0
    )

    # ── Keyword coverage from raw texts ───────────────────────
    keyword_score = _keyword_coverage_score(resume_text, jd_text)

    # ── Strengths — top matched skills as highlights ──────────
    matched_original = [
        s for s in jd_required_skills
        if _normalize(s) in matched_norm
    ]
    missing_original = [
        s for s in jd_required_skills
        if _normalize(s) in missing_norm
    ]
    preferred_matched_original = [
        s for s in jd_preferred
        if _normalize(s) in preferred_matched_norm
    ]

    strengths = matched_original[:8]  # Top 8 matched mandatory skills

    # Weaknesses = missing mandatory skills (most impactful for ATS)
    weaknesses = missing_original[:8]

    # Interview focus = missing skills the candidate will be tested on
    interview_focus = missing_original[:5] + [
        s for s in jd_preferred if _normalize(s) not in preferred_matched_norm
    ][:3]

    # ── Confidence — based on data completeness ───────────────
    confidence = _compute_confidence(resume_skills, jd_required_skills)

    return {
        "matched_skills": matched_original,
        "missing_skills": missing_original,
        "preferred_matched": preferred_matched_original,
        "ats_overlap_score": ats_score,
        "keyword_coverage_score": keyword_score,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "interview_focus_areas": interview_focus[:6],
        "confidence": confidence,
    }


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _normalize(skill: str) -> str:
    """Lowercase, strip punctuation, replace spaces with underscores."""
    return re.sub(r"[^\w]", "_", skill.lower().strip()).strip("_")


def _fuzzy_match(skill_norm: str, candidate_norms: Set[str]) -> bool:
    """
    Check if skill_norm is a substring of any candidate skill or vice versa.
    Handles cases like 'react' matching 'react_19' or 'reactjs'.
    """
    skill_parts = skill_norm.replace("_", "")
    for c in candidate_norms:
        c_parts = c.replace("_", "")
        if skill_parts in c_parts or c_parts in skill_parts:
            return True
    return False


def _keyword_coverage_score(resume_text: str, jd_text: str) -> int:
    """
    Compute token-level keyword overlap between resume and JD text.
    Returns a 0-100 integer score.
    """
    if not resume_text or not jd_text:
        return 0

    # Extract meaningful tokens (3+ chars, alpha only, deduplicated)
    def _tokens(text: str) -> Set[str]:
        return {
            w.lower() for w in re.findall(r"\b[a-z]{3,}\b", text.lower())
            if w not in _STOP_WORDS
        }

    jd_tokens = _tokens(jd_text)
    resume_tokens = _tokens(resume_text)
    if not jd_tokens:
        return 0
    overlap = jd_tokens & resume_tokens
    return min(100, int(len(overlap) / len(jd_tokens) * 100))


def _compute_confidence(resume_skills: List[str], jd_skills: List[str]) -> float:
    """Confidence score based on list completeness."""
    if not resume_skills and not jd_skills:
        return 0.3
    if not resume_skills or not jd_skills:
        return 0.5
    if len(resume_skills) >= 3 and len(jd_skills) >= 3:
        return 0.95
    return 0.75


# Common English stop words to exclude from keyword coverage scoring
_STOP_WORDS = {
    "the", "and", "for", "with", "that", "this", "from", "have", "will",
    "you", "are", "our", "all", "your", "can", "not", "but", "has", "its",
    "been", "work", "team", "role", "able", "also", "new", "use", "help",
    "build", "experience", "strong", "knowledge", "ability", "skills",
    "excellent", "including", "years", "company", "required", "preferred",
}
