"""
Resume Agent (Section 10.2)
Converts raw resume text → structured ResumeAnalysis via LLM execution.
Evaluates resume_quality_score (formatting, section completeness, clarity, technical depth).
No ATS score (ATS score requires a Job Description in Sprint 0.3).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.core.llm_client import LLMClient
from app.graph.state import InterviewState
from app.prompts.loader import get_developer_prompt, get_system_prompt

# ── Output schema ─────────────────────────────────────────────


class ExperienceEntry(BaseModel):
    id: str | None = None
    title: str = ""
    company: str = ""
    period: str = ""
    start_date: str = ""
    end_date: str = ""
    is_current: bool = False
    employment_type: str = ""
    description: str = ""
    highlights: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    ownership_bullets: list[str] = Field(
        default_factory=list,
        description="Factual evidence of independent feature or service ownership",
    )
    architecture_bullets: list[str] = Field(
        default_factory=list,
        description="Factual evidence of system design, database architecture, or microservice design",
    )
    leadership_bullets: list[str] = Field(
        default_factory=list,
        description="Factual evidence of mentoring, code reviews, or team leadership",
    )
    complexity_bullets: list[str] = Field(
        default_factory=list,
        description="Factual evidence of high scale, performance optimization, or complex technical delivery",
    )


class EducationEntry(BaseModel):
    id: str | None = None
    degree: str = ""
    institution: str = ""
    field_of_study: str = ""
    graduation_year: str = ""
    gpa: str | None = None


class ProjectEntry(BaseModel):
    id: str | None = None
    title: str = ""
    description: str = ""
    technologies: list[str] = Field(default_factory=list)
    link: str | None = None
    role: str | None = None


class CertificationEntry(BaseModel):
    id: str | None = None
    name: str = ""
    issuer: str = ""
    issue_date: str = ""


class ResumeAnalysis(BaseModel):
    summary: str = Field(
        default="", description="Executive candidate summary extracted from resume"
    )
    technical_skills: list[str] = Field(
        default_factory=list, description="All technical skills and technologies"
    )
    soft_skills: list[str] = Field(
        default_factory=list,
        description="Soft skills, domain competencies, and leadership qualities",
    )
    experience: list[ExperienceEntry] = Field(
        default_factory=list, description="List of work experience entries"
    )
    education: list[EducationEntry] = Field(
        default_factory=list, description="List of education and academic credentials"
    )
    projects: list[ProjectEntry] = Field(default_factory=list, description="List of key projects")
    certifications: list[CertificationEntry] = Field(
        default_factory=list, description="List of certifications"
    )
    languages: list[str] = Field(default_factory=list, description="Spoken/written human languages")
    strengths: list[str] = Field(
        default_factory=list, description="Key candidate strengths identified"
    )
    weaknesses: list[str] = Field(
        default_factory=list, description="Areas for candidate improvement"
    )
    career_level: str | None = Field(
        default="UNKNOWN",
        description="Deprecated. Final seniority is computed deterministically by SeniorityEngine in Python.",
    )
    resume_quality_score: int = Field(
        default=85,
        ge=0,
        le=100,
        description="Calculated resume formatting, clarity, section completeness, and technical depth score (0 to 100)",
    )


# ── Agent ─────────────────────────────────────────────────────


class ResumeAgent(BaseAgent):
    agent_name = "ResumeAgent"
    prompt_version = "v1"

    def _temperature(self) -> float:
        return 0.1  # deterministic extraction

    def _run(self, state: InterviewState, retry_feedback: str | None = None) -> dict:
        raw_text = state.get("resume_raw_text", "")
        if not raw_text:
            raise ValueError("resume_raw_text is missing from state")

        messages = LLMClient.build_messages(
            system_prompt=get_system_prompt("resume_agent", self.prompt_version),
            developer_prompt=get_developer_prompt("resume_agent", self.prompt_version),
            user_content=f"Resume Raw Text:\n{raw_text}",
        )

        analysis: ResumeAnalysis = self._invoke_structured(messages, ResumeAnalysis, retry_feedback)

        return {"resume_data": analysis.model_dump()}

    def _on_failure(self, state: InterviewState, error: str) -> dict:
        return {
            "resume_data": ResumeAnalysis().model_dump(),
            "error_log": [{"agent": self.agent_name, "error": error}],
        }
