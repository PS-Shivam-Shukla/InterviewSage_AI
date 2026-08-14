"""
Seniority Evaluation Engine (Section 10.3)
Pure deterministic Python engine for calculating candidate seniority.

Features:
- Date string parsing & non-overlapping employment interval merging
- Role relevance filtering (technical/software roles vs non-technical roles)
- 100-point rubric scoring:
  1. Relevant Experience (40 pts max)
  2. Independent Ownership (20 pts max)
  3. System Design & Architecture (15 pts max)
  4. Leadership & Mentoring (15 pts max)
  5. Technical Complexity & Impact (10 pts max)
- Guardrails Engine (Staff & Senior threshold enforcement; Title != Truth)
- Explainable evidence and limitations bullet lists
"""

import datetime
import re
from typing import Any

from pydantic import BaseModel, Field

# ── Data Models ──────────────────────────────────────────────────


class SeniorityBreakdown(BaseModel):
    experience_score: int = Field(..., ge=0, le=40)
    ownership_score: int = Field(..., ge=0, le=20)
    architecture_score: int = Field(..., ge=0, le=15)
    leadership_score: int = Field(..., ge=0, le=15)
    complexity_score: int = Field(..., ge=0, le=10)


class ExperienceMetrics(BaseModel):
    total_months: int = Field(..., ge=0)
    relevant_months: int = Field(..., ge=0)


class SeniorityEvaluationResult(BaseModel):
    seniority_signal: str  # INTERN | JUNIOR | MID | SENIOR | STAFF
    seniority_score: int = Field(..., ge=0, le=100)
    experience_metrics: ExperienceMetrics
    seniority_breakdown: SeniorityBreakdown
    seniority_evidence: list[str] = Field(default_factory=list)
    seniority_limitations: list[str] = Field(default_factory=list)


# ── Helper Functions ──────────────────────────────────────────────

MONTH_MAP = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "september": 9,
    "sept": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def parse_month_year(
    date_str: str, default_to_present: bool = False, ref_date: datetime.date | None = None
) -> datetime.date | None:
    """Parse string representations of dates like 'Jan 2022', '2022-01', '01/2022', '2022', 'Present'."""
    if not date_str or not isinstance(date_str, str):
        return ref_date if (default_to_present and ref_date) else None

    clean = date_str.strip().lower()

    if clean in ("present", "current", "now", "today", "ongoing"):
        return ref_date or datetime.date.today()

    # Match YYYY-MM
    m1 = re.search(r"(\d{4})[-/](\d{1,2})", clean)
    if m1:
        year, month = int(m1.group(1)), int(m1.group(2))
        return datetime.date(year, max(1, min(12, month)), 1)

    # Match Month YYYY or YYYY Month (e.g., 'Jan 2022', 'July 2026')
    m2 = re.search(r"([a-z]+)\s*(\d{4})", clean)
    if m2:
        month_str, year_str = m2.group(1), m2.group(2)
        month = MONTH_MAP.get(month_str, 1)
        return datetime.date(int(year_str), month, 1)

    m3 = re.search(r"(\d{4})\s*([a-z]+)", clean)
    if m3:
        year_str, month_str = m3.group(1), m3.group(2)
        month = MONTH_MAP.get(month_str, 1)
        return datetime.date(int(year_str), month, 1)

    # Match standalone YYYY
    m4 = re.search(r"\b(\d{4})\b", clean)
    if m4:
        year = int(m4.group(1))
        month = 12 if default_to_present else 1
        return datetime.date(year, month, 1)

    return ref_date if (default_to_present and ref_date) else None


def merge_employment_intervals(intervals: list[tuple[datetime.date, datetime.date]]) -> int:
    """Merge overlapping (start_date, end_date) tuples and calculate total non-overlapping months."""
    if not intervals:
        return 0

    valid_intervals = []
    for start, end in intervals:
        if start and end and start <= end:
            valid_intervals.append((start, end))

    if not valid_intervals:
        return 0

    # Sort by start date
    valid_intervals.sort(key=lambda x: x[0])

    merged = [valid_intervals[0]]
    for current in valid_intervals[1:]:
        prev_start, prev_end = merged[-1]
        curr_start, curr_end = current

        if curr_start <= prev_end:
            # Overlapping or contiguous interval -> merge
            merged[-1] = (prev_start, max(prev_end, curr_end))
        else:
            merged.append(current)

    total_months = 0
    for start, end in merged:
        # Month calculation inclusive of partial months
        months = (end.year - start.year) * 12 + (end.month - start.month) + 1
        total_months += max(1, months)

    return total_months


TECHNICAL_ROLE_KEYWORDS = {
    "developer",
    "engineer",
    "architect",
    "programmer",
    "coder",
    "software",
    "backend",
    "frontend",
    "full stack",
    "fullstack",
    "ai",
    "ml",
    "machine learning",
    "data engineer",
    "devops",
    "cloud",
    "sre",
    "systems",
    "tech lead",
    "cto",
    "vp of engineering",
    "technical lead",
    "data scientist",
    "security engineer",
}


NON_TECHNICAL_TITLE_KEYWORDS = {
    "sales",
    "marketing",
    "recruiter",
    "talent",
    "human resources",
    "hr",
    "accountant",
    "finance",
    "legal",
    "customer support",
    "customer service",
    "account executive",
    "operations manager",
}


def is_technical_role(title: str, description: str = "", technologies: list[str] = None) -> bool:
    """Determine if a job experience entry is technical/software engineering relevant."""
    title_clean = (title or "").lower()

    # Exclude explicit non-technical roles unless title explicitly contains engineering/development keywords
    if any(nk in title_clean for nk in NON_TECHNICAL_TITLE_KEYWORDS):
        if not any(
            tk in title_clean
            for tk in ["engineer", "developer", "architect", "programmer", "tech lead", "cto"]
        ):
            return False

    combined = f"{title_clean} {' '.join(technologies or [])}".lower()
    if any(kw in combined for kw in TECHNICAL_ROLE_KEYWORDS):
        return True

    # Secondary check on description only if explicit technologies are present
    if technologies and any(kw in description.lower() for kw in TECHNICAL_ROLE_KEYWORDS):
        return True

    return False


# ── Seniority Engine ──────────────────────────────────────────────


class SeniorityEngine:

    @classmethod
    def evaluate(
        cls,
        resume_data: dict[str, Any],
        target_role: str | None = None,
        ref_date: datetime.date | None = None,
    ) -> dict[str, Any]:
        """
        Main entry point. Takes parsed resume JSON dict and computes deterministic seniority evaluation.
        """
        ref_date = ref_date or datetime.date.today()

        # 1. Experience Interval Calculations
        raw_experience = resume_data.get("experience") or []
        all_intervals: list[tuple[datetime.date, datetime.date]] = []
        relevant_intervals: list[tuple[datetime.date, datetime.date]] = []

        dedup_entries = []
        seen_keys = set()

        for exp in raw_experience:
            if not isinstance(exp, dict):
                continue
            title = exp.get("title") or exp.get("role") or ""
            company = exp.get("company") or ""
            period = exp.get("period") or ""
            key = f"{title.lower()}|{company.lower()}|{period.lower()}"
            if key in seen_keys:
                continue
            seen_keys.add(key)
            dedup_entries.append(exp)

            start_str = exp.get("start_date") or ""
            end_str = exp.get("end_date") or ""
            if not start_str and period:
                parts = re.split(r"[-–—to]+", period, maxsplit=1)
                start_str = parts[0].strip() if len(parts) > 0 else ""
                end_str = parts[1].strip() if len(parts) > 1 else ""

            start_date = parse_month_year(start_str, default_to_present=False, ref_date=ref_date)
            end_date = parse_month_year(end_str, default_to_present=True, ref_date=ref_date)

            if start_date and end_date:
                if start_date > end_date:
                    start_date, end_date = end_date, start_date
                all_intervals.append((start_date, end_date))

                desc = exp.get("description") or ""
                techs = exp.get("technologies") or []
                if is_technical_role(title, desc, techs):
                    relevant_intervals.append((start_date, end_date))

        total_months = merge_employment_intervals(all_intervals)
        relevant_months = merge_employment_intervals(relevant_intervals)

        # Fallback for resumes without explicit date ranges
        if total_months == 0 and dedup_entries:
            total_months = len(dedup_entries) * 12
            relevant_months = total_months

        # 2. Rubric Category Scoring
        exp_score = cls._score_experience_duration(relevant_months)
        ownership_score, ownership_evidence = cls._score_ownership(dedup_entries)
        architecture_score, arch_evidence = cls._score_architecture(dedup_entries)
        leadership_score, lead_evidence = cls._score_leadership(dedup_entries)
        complexity_score, comp_evidence = cls._score_complexity(dedup_entries, resume_data)

        raw_score = (
            exp_score + ownership_score + architecture_score + leadership_score + complexity_score
        )
        raw_score = max(0, min(100, raw_score))

        # 3. Guardrails & Threshold Evaluation
        final_signal, capped_score, guardrail_limitations = cls._apply_guardrails(
            score=raw_score,
            relevant_months=relevant_months,
            ownership_score=ownership_score,
            architecture_score=architecture_score,
            leadership_score=leadership_score,
        )

        # 4. Evidence Aggregation
        all_evidence = []

        # Duration Evidence
        years = relevant_months // 12
        rem_mos = relevant_months % 12
        if relevant_months > 0:
            time_str = f"{years} yrs {rem_mos} mos" if years > 0 else f"{rem_mos} mos"
            all_evidence.append(f"{time_str} of relevant software engineering experience")
        else:
            all_evidence.append("Limited or non-technical relevant employment history recorded")

        all_evidence.extend(ownership_evidence)
        all_evidence.extend(arch_evidence)
        all_evidence.extend(lead_evidence)
        all_evidence.extend(comp_evidence)

        # Deduplicate evidence bullets cleanly
        unique_evidence = []
        for ev in all_evidence:
            if ev and ev not in unique_evidence:
                unique_evidence.append(ev)

        return {
            "seniority_signal": final_signal,
            "seniority_score": capped_score,
            "experience_metrics": {
                "total_months": total_months,
                "relevant_months": relevant_months,
            },
            "seniority_breakdown": {
                "experience_score": exp_score,
                "ownership_score": ownership_score,
                "architecture_score": architecture_score,
                "leadership_score": leadership_score,
                "complexity_score": complexity_score,
            },
            "seniority_evidence": unique_evidence,
            "seniority_limitations": guardrail_limitations,
        }

    # ── Category Scorers ──────────────────────────────────────────────

    @staticmethod
    def _score_experience_duration(relevant_months: int) -> int:
        if relevant_months < 6:
            return 0
        elif relevant_months < 18:
            return 5
        elif relevant_months < 36:
            return 12
        elif relevant_months < 60:
            return 22
        elif relevant_months < 96:
            return 32
        else:
            return 40

    @staticmethod
    def _score_ownership(entries: list[dict[str, Any]]) -> tuple[int, list[str]]:
        score = 0
        evidence = []
        combined_text = " ".join(
            [
                f"{e.get('title','')} {e.get('description','')} {' '.join(e.get('highlights',[]))} {' '.join(e.get('ownership_bullets',[]))}"
                for e in entries
            ]
        ).lower()

        if any(
            kw in combined_text
            for kw in [
                "end-to-end",
                "end to end",
                "owned major",
                "core service owner",
                "lead architect",
            ]
        ):
            score = 20
            evidence.append("Major system & core service end-to-end ownership")
        elif any(
            kw in combined_text
            for kw in [
                "owned",
                "owner",
                "designed and built",
                "built and deployed",
                "sole developer",
            ]
        ):
            score = 15
            evidence.append("End-to-end feature and service ownership")
        elif any(
            kw in combined_text
            for kw in ["independent", "independently", "responsible for", "implemented feature"]
        ):
            score = 10
            evidence.append("Independent feature ownership & delivery")
        elif entries:
            score = 5
            evidence.append("Task-level execution and module delivery")

        return score, evidence

    @staticmethod
    def _score_architecture(entries: list[dict[str, Any]]) -> tuple[int, list[str]]:
        score = 0
        evidence = []
        combined_text = " ".join(
            [
                f"{e.get('title','')} {e.get('description','')} {' '.join(e.get('highlights',[]))} {' '.join(e.get('architecture_bullets',[]))}"
                for e in entries
            ]
        ).lower()

        if any(
            kw in combined_text
            for kw in [
                "multi-system",
                "distributed systems",
                "event-driven",
                "microservices architecture",
                "rag system",
            ]
        ):
            score = 15
            evidence.append("Strong multi-component system architecture ownership")
        elif any(
            kw in combined_text
            for kw in [
                "designed architecture",
                "database architecture",
                "api architecture",
                "schema design",
                "rest api",
            ]
        ):
            score = 10
            evidence.append("Regular system design & API architecture responsibility")
        elif any(kw in combined_text for kw in ["architecture", "design", "refactored"]):
            score = 5
            evidence.append("Basic system design involvement")

        return score, evidence

    @staticmethod
    def _score_leadership(entries: list[dict[str, Any]]) -> tuple[int, list[str]]:
        score = 0
        evidence = []
        combined_text = " ".join(
            [
                f"{e.get('title','')} {e.get('description','')} {' '.join(e.get('highlights',[]))} {' '.join(e.get('leadership_bullets',[]))}"
                for e in entries
            ]
        ).lower()

        if any(
            kw in combined_text
            for kw in [
                "tech lead",
                "technical lead",
                "engineering manager",
                "cross-team",
                "led team",
                "supervising",
            ]
        ):
            score = 15
            evidence.append("Team & technical engineering leadership")
        elif any(
            kw in combined_text
            for kw in ["mentored", "code review", "guided developers", "onboarded"]
        ):
            score = 10
            evidence.append("Regular mentoring & code review leadership")
        elif any(kw in combined_text for kw in ["reviewed", "collaborated"]):
            score = 5
            evidence.append("Occasional peer code review involvement")

        return score, evidence

    @staticmethod
    def _score_complexity(
        entries: list[dict[str, Any]], resume_data: dict[str, Any]
    ) -> tuple[int, list[str]]:
        score = 2
        evidence = []
        tech_skills = resume_data.get("technical_skills") or []
        combined_text = (
            f"{' '.join(tech_skills)} "
            + " ".join(
                [f"{e.get('description','')} {' '.join(e.get('highlights',[]))}" for e in entries]
            ).lower()
        )

        if any(
            kw in combined_text
            for kw in [
                "scale",
                "high traffic",
                "millions",
                "latency",
                "vector search",
                "llm",
                "rag",
                "optimization",
            ]
        ):
            score = 10
            evidence.append("High scale / high complexity production system delivery")
        elif any(
            kw in combined_text
            for kw in ["docker", "fastapi", "postgresql", "pipeline", "etl", "microservice"]
        ):
            score = 8
            evidence.append("High complexity backend microservice engineering")
        elif len(tech_skills) > 4:
            score = 5
            evidence.append("Moderate technical complexity across full stack tools")

        return score, evidence

    # ── Guardrails ────────────────────────────────────────────────────

    @classmethod
    def _apply_guardrails(
        cls,
        score: int,
        relevant_months: int,
        ownership_score: int,
        architecture_score: int,
        leadership_score: int,
    ) -> tuple[str, int, list[str]]:
        """Apply strict guardrail rules for STAFF and SENIOR classification."""
        limitations = []

        # Determine raw level signal from rubric score
        if score >= 80:
            signal = "STAFF"
        elif score >= 60:
            signal = "SENIOR"
        elif score >= 35:
            signal = "MID"
        elif score >= 15:
            signal = "JUNIOR"
        else:
            signal = "INTERN"

        # STAFF Guardrail: Requires explicit cross-team/multi-system leadership or architecture
        if signal == "STAFF":
            if leadership_score < 10 or architecture_score < 10:
                signal = "SENIOR"
                score = min(score, 79)
                limitations.append(
                    "Capped at SENIOR: Missing evidence of cross-team leadership or multi-system architecture strategy."
                )

        # SENIOR Guardrail: Requires >= 36 relevant experience months AND (ownership >= 10 OR architecture >= 5)
        if signal == "SENIOR":
            if relevant_months < 36:
                signal = "MID"
                score = min(score, 59)
                limitations.append("Capped at MID: Requires >= 36 relevant experience months.")
            elif ownership_score < 10 and architecture_score < 5:
                signal = "MID"
                score = min(score, 59)
                limitations.append(
                    "Capped at MID: Requires explicit feature ownership or system design responsibility."
                )

        if not limitations and signal in ("JUNIOR", "INTERN"):
            limitations.append("Early career history with task-level execution focus.")

        return signal, score, limitations
