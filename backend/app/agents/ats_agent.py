"""
ATS Agent (Phase 5)
Computes resume ↔ JD alignment using the map_skills MCP tool
(deterministic computation) and appends HITL flag if score is too low.

Architecture contract:
  - Calls map_skills MCP tool for skill matrix computation.
  - If ats_overlap_score < 30, flags hitl_required to warn the candidate.
  - Does NOT call LLM for scoring — scoring is deterministic in MCP tool.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.graph.state import InterviewState
from app.mcp import mcp_server

# ── Output schema ─────────────────────────────────────────────


class ATSAnalysis(BaseModel):
    ats_overlap_score: int = Field(0, ge=0, le=100)
    keyword_coverage_score: int = Field(0, ge=0, le=100)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    preferred_matched: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    interview_focus_areas: list[str] = Field(default_factory=list)
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    incomplete_data: bool = False


# ── Agent ─────────────────────────────────────────────────────


class ATSAgent(BaseAgent):
    agent_name = "ATSAgent"
    prompt_version = "v1"

    def _temperature(self) -> float:
        return 0.1

    def _run(self, state: InterviewState, retry_feedback: str | None = None) -> dict:
        resume_data = state.get("resume_data") or {}
        jd_data = state.get("jd_data") or {}

        if not resume_data or not jd_data:
            return {
                "ats_analysis": ATSAnalysis(incomplete_data=True).model_dump(),
                "hitl_required": True,
                "hitl_reason": "Missing resume or JD data — cannot compute ATS alignment.",
                "error_log": [{"agent": self.agent_name, "warning": "Missing resume or JD data"}],
            }

        # ── Full skill matrix via map_skills MCP tool ─────────
        resume_skills_raw = resume_data.get("skills") or resume_data.get("technical_skills") or []
        # Handle skills as dict (old schema) or list (new schema)
        if isinstance(resume_skills_raw, dict):
            all_skills: list[str] = []
            for v in resume_skills_raw.values():
                if isinstance(v, list):
                    all_skills.extend(str(s) for s in v)
                elif isinstance(v, str):
                    all_skills.append(v)
            resume_skills_raw = all_skills

        # Normalize and strip category headers (e.g. "Languages: Python, SQL")
        resume_skills: list[str] = []
        for item in (resume_skills_raw if isinstance(resume_skills_raw, list) else [str(resume_skills_raw)]):
            if not item:
                continue
            cleaned = str(item).split(":", 1)[-1] if ":" in str(item) else str(item)
            for part in cleaned.split(","):
                part_stripped = part.strip()
                if part_stripped and part_stripped not in resume_skills:
                    resume_skills.append(part_stripped)

        jd_required = jd_data.get("required_skills", []) or jd_data.get("mandatory_skills", [])
        jd_preferred = jd_data.get("preferred_skills", [])

        tool_result = mcp_server.call_tool(
            "map_skills",
            resume_skills=resume_skills,
            jd_required_skills=jd_required,
            jd_preferred_skills=jd_preferred,
            resume_text=state.get("resume_raw_text", ""),
            jd_text=state.get("jd_raw_text", ""),
        )

        if not tool_result.success:
            raise ValueError(f"map_skills tool failed: {tool_result.error}")

        mapping = tool_result.output
        analysis = ATSAnalysis(
            ats_overlap_score=mapping["ats_overlap_score"],
            keyword_coverage_score=mapping.get("keyword_coverage_score", 0),
            matched_skills=mapping["matched_skills"],
            missing_skills=mapping["missing_skills"],
            preferred_matched=mapping.get("preferred_matched", []),
            strengths=mapping["strengths"],
            weaknesses=mapping["weaknesses"],
            interview_focus_areas=mapping["interview_focus_areas"],
            confidence=mapping["confidence"],
        )

        result: dict = {"ats_analysis": analysis.model_dump()}

        # HITL: very low ATS score is a strong signal to warn candidate
        if analysis.ats_overlap_score < 30:
            result["hitl_required"] = True
            result["hitl_reason"] = (
                f"ATS overlap is only {analysis.ats_overlap_score}%. "
                f"Missing critical skills: {analysis.missing_skills[:5]}. "
                "Review your resume or job selection before continuing."
            )

        return result

    def _on_failure(self, state: InterviewState, error: str) -> dict:
        return {
            "ats_analysis": ATSAnalysis(incomplete_data=True).model_dump(),
            "error_log": [{"agent": self.agent_name, "error": error}],
        }
