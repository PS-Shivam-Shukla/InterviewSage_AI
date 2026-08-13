"""
JD Analysis Agent (Section 10.3)
Converts raw job description text → structured JDAnalysis including negative skill domain inference.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from app.agents.base import BaseAgent
from app.core.llm_client import LLMClient
from app.graph.state import InterviewState
from app.prompts.loader import get_system_prompt, get_developer_prompt

# Static domain exclusion map for RID-02
_DOMAIN_EXCLUSIONS = {
    "backend": ["React", "Vue", "Angular", "CSS", "HTML", "Frontend", "UI"],
    "frontend": ["Django", "FastAPI", "PostgreSQL", "Kafka", "Backend", "SQL"],
    "devops": ["React", "Vue", "Frontend", "UI", "CSS"],
}


class JDAnalysis(BaseModel):
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    negative_skills: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    seniority_level: str = "NOT_SPECIFIED"
    target_role: str = ""
    industry: str = "NOT_SPECIFIED"
    company_values: List[str] = Field(default_factory=list)

    @field_validator("seniority_level")
    @classmethod
    def validate_seniority(cls, v: str) -> str:
        allowed = {"JUNIOR", "MID", "SENIOR", "STAFF", "NOT_SPECIFIED"}
        return v.upper() if v.upper() in allowed else "NOT_SPECIFIED"


class JDAgent(BaseAgent):
    agent_name = "JDAgent"
    prompt_version = "v1"

    def _temperature(self) -> float:
        return 0.1

    def _infer_negative_skills(self, role: str, required_skills: List[str]) -> List[str]:
        """Auto-infers negative skill domain exclusions based on target role."""
        role_lower = role.lower()
        skills_str = " ".join(s.lower() for s in required_skills)
        negative: set[str] = set()

        if "backend" in role_lower or "python" in skills_str or "fastapi" in skills_str:
            for s in _DOMAIN_EXCLUSIONS["backend"]:
                if s.lower() not in skills_str:
                    negative.add(s)
        elif "frontend" in role_lower or "react" in skills_str:
            for s in _DOMAIN_EXCLUSIONS["frontend"]:
                if s.lower() not in skills_str:
                    negative.add(s)

        return list(negative)

    def _run(self, state: InterviewState, retry_feedback: Optional[str] = None) -> dict:
        raw_text = state.get("jd_raw_text", "")
        if not raw_text:
            raise ValueError("jd_raw_text is missing from state")

        messages = LLMClient.build_messages(
            system_prompt=get_system_prompt("jd_agent", self.prompt_version),
            developer_prompt=get_developer_prompt("jd_agent", self.prompt_version),
            user_content=f"Job description:\n{raw_text}",
        )

        analysis: JDAnalysis = self._invoke_structured(messages, JDAnalysis, retry_feedback)

        if not analysis.negative_skills:
            analysis.negative_skills = self._infer_negative_skills(
                analysis.target_role, analysis.required_skills
            )

        return {"jd_data": analysis.model_dump()}

    def _on_failure(self, state: InterviewState, error: str) -> dict:
        return {
            "jd_data": JDAnalysis().model_dump(),
            "error_log": [{"agent": self.agent_name, "error": error}],
        }
