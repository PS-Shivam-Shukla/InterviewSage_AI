"""
Profile Intelligence Agent (Section 10.5)
Synthesises resume + JD + ATS + industry standards →
a holistic candidate profile used to calibrate question difficulty.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.core.llm_client import LLMClient
from app.graph.state import InterviewState
from app.mcp import mcp_server
from app.prompts.loader import get_developer_prompt, get_system_prompt

# ── Output schema ─────────────────────────────────────────────


class ProfileSummary(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    growth_edges: list[str] = Field(default_factory=list)
    calibrated_seniority: str = "MID"
    industry_positioning: str = ""
    difficulty_recommendation: str = "MEDIUM"

    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        allowed = {"EASY", "MEDIUM", "HARD", "ADVANCED"}
        return v.upper() if v.upper() in allowed else "MEDIUM"


# ── Agent ─────────────────────────────────────────────────────


class ProfileIntelligenceAgent(BaseAgent):
    agent_name = "ProfileIntelligenceAgent"
    prompt_version = "v1"

    def _temperature(self) -> float:
        return 0.2

    def _run(self, state: InterviewState, retry_feedback: str | None = None) -> dict:
        resume_data = state.get("resume_data") or {}
        jd_data = state.get("jd_data") or {}
        ats_analysis = state.get("ats_analysis") or {}

        # Fetch industry standards via MCP resource
        role = jd_data.get("target_role", "")
        industry_standards = (
            mcp_server.read_resource(
                f"resource://industry-standards/{role.lower().replace(' ', '-')}"
            )
            or {}
        )

        user_content = (
            f"Resume data:\n{resume_data}\n\n"
            f"JD data:\n{jd_data}\n\n"
            f"ATS analysis:\n{ats_analysis}\n\n"
            f"Industry standards for '{role}':\n{industry_standards}"
        )
        developer = get_developer_prompt("profile_intelligence_agent", self.prompt_version) or (
            "Synthesise the candidate profile. Return JSON with: "
            "strengths (list), growth_edges (list), calibrated_seniority "
            "(JUNIOR|MID|SENIOR|STAFF), industry_positioning (string), "
            "difficulty_recommendation (EASY|MEDIUM|HARD|ADVANCED)."
        )

        messages = LLMClient.build_messages(
            system_prompt=get_system_prompt("profile_intelligence_agent", self.prompt_version),
            developer_prompt=developer,
            user_content=user_content,
        )

        profile: ProfileSummary = self._invoke_structured(messages, ProfileSummary, retry_feedback)
        profile_dict = profile.model_dump()

        # AUTHORITATIVE SINGLE SOURCE OF TRUTH: SeniorityEngine
        # Override any LLM-synthesised seniority with SeniorityEngine's calculated signal
        engine_seniority = (resume_data.get("seniority_signal") or "MID").upper()
        profile_dict["calibrated_seniority"] = engine_seniority
        profile_dict["seniority_score"] = resume_data.get("seniority_score", 0)
        profile_dict["relevant_experience_months"] = resume_data.get(
            "relevant_experience_months", 0
        )

        return {"profile_summary": profile_dict}

    def _on_failure(self, state: InterviewState, error: str) -> dict:
        resume_data = state.get("resume_data") or {}
        authoritative_seniority = (resume_data.get("seniority_signal") or "MID").upper()
        return {
            "profile_summary": ProfileSummary(
                calibrated_seniority=authoritative_seniority
            ).model_dump(),
            "error_log": [{"agent": self.agent_name, "error": error}],
        }
